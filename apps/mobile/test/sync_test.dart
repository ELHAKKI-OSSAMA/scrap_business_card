import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:ocr_suite_mobile/src/api/api_client.dart';
import 'package:ocr_suite_mobile/src/app_state.dart';
import 'package:ocr_suite_mobile/src/drafts/draft.dart';
import 'package:ocr_suite_mobile/src/drafts/draft_store.dart';
import 'package:ocr_suite_mobile/src/sync/sync_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fakes.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory tmp;
  late DraftStore store;
  late FakeServer server;
  late SyncService sync;

  setUp(() async {
    tmp = await Directory.systemTemp.createTemp('ocr_sync_test');
    store = DraftStore(Directory('${tmp.path}/drafts'));
    await store.load();
    server = FakeServer();
    sync = SyncService(store: store, api: server, pollInterval: Duration.zero, maxPolls: 3);
  });
  tearDown(() async {
    // Windows keeps a file locked for a moment after a background read finishes: retry briefly
    for (var i = 0; ; i++) {
      try {
        await tmp.delete(recursive: true);
        return;
      } on FileSystemException {
        if (i >= 20) rethrow;
        await Future<void>.delayed(const Duration(milliseconds: 50));
      }
    }
  });

  Future<Draft> queued({bool back = true}) async {
    final d = Draft(localId: 'local1', product: 'business_card');
    for (final side in back ? ['front', 'back'] : ['front']) {
      final src = File('${tmp.path}/$side.jpg')..writeAsBytesSync(List.filled(64, side.length));
      await store.importImage(d, side, src);
    }
    d.status = DraftStatus.pendingUpload;
    await store.save(d);
    return d;
  }

  test('draft store persists atomically and reloads', () async {
    await queued();
    final reloaded = DraftStore(Directory('${tmp.path}/drafts'));
    await reloaded.load();
    expect(reloaded.all.single.localId, 'local1');
    expect(reloaded.all.single.images.keys, containsAll(['front', 'back']));
    expect(File('${tmp.path}/drafts/drafts.json.tmp').existsSync(), isFalse);
  });

  test('local drafts are never uploaded until submitted', () async {
    final d = await queued();
    d.status = DraftStatus.localDraft;
    await store.save(d);
    await sync.syncAll();
    expect(server.creates, 0);
    expect(store.all.single.status, DraftStatus.localDraft);
  });

  test('offline keeps the draft queued and nothing is lost', () async {
    await queued();
    server.offline = true;
    expect(await sync.syncAll(), isFalse);
    expect(sync.lastError, startsWith('network'));
    final reloaded = DraftStore(Directory('${tmp.path}/drafts'));
    await reloaded.load();
    expect(reloaded.all.single.status, DraftStatus.pendingUpload);
    expect(reloaded.all.single.images.length, 2);
  });

  test('status transitions pendingUpload -> processing -> completed', () async {
    await queued();
    final seen = <DraftStatus>[];
    sync.addListener(() {
      final s = store.all.single.status;
      if (seen.isEmpty || seen.last != s) seen.add(s);
    });
    server.resultData = {'full_name': {'value': 'X'}};
    expect(await sync.syncAll(), isTrue);
    expect(seen, containsAllInOrder([DraftStatus.pendingUpload, DraftStatus.processing, DraftStatus.completed]));
    final d = store.all.single;
    expect(d.serverId, 'doc-1');
    expect(d.result?['full_name']['value'], 'X');
    expect(server.uploads, 2);
  });

  test('interrupted batch resumes without duplicate documents or re-uploads', () async {
    await queued();
    server.failUploadsAfter = 1; // front succeeds, back drops
    expect(await sync.syncAll(), isFalse);
    expect(store.all.single.uploadedSha.keys, ['front']);
    expect(store.all.single.status, DraftStatus.pendingUpload);
    server.failUploadsAfter = -1;
    expect(await sync.syncAll(), isTrue);
    expect(server.docs.length, 1, reason: 'client_ref idempotency: one server document');
    expect(server.uploads, 2, reason: 'front not re-uploaded');
    expect(server.processes, 1);
  });

  test('document created but app killed before saving serverId: replay reuses the document', () async {
    final d = await queued(back: false);
    await server.createDocument('business-cards', clientRef: d.localId); // server side already has it
    await sync.syncAll();
    expect(server.docs.length, 1);
  });

  test('replaying a completed sync does nothing', () async {
    await queued(back: false);
    await sync.syncAll();
    await sync.syncAll();
    expect(server.creates, 1);
    expect(server.uploads, 1);
    expect(server.processes, 1);
  });

  test('failed job marks the draft failed and retry requeues it', () async {
    await queued(back: false);
    server.jobStatus = 'failed';
    await sync.syncAll();
    final d = store.all.single;
    expect(d.status, DraftStatus.failed);
    expect(d.error, 'ocr_error');
    await sync.retry(d);
    expect(d.status, DraftStatus.pendingUpload);
    expect(d.error, isNull);
    server.jobStatus = 'completed';
    await sync.syncAll();
    expect(store.all.single.status, DraftStatus.completed);
    expect(server.uploads, 1, reason: 'unchanged image is not re-uploaded');
  });

  test('replacing an image after upload forces re-upload of that side only', () async {
    final d = await queued();
    await sync.syncAll();
    final src = File('${tmp.path}/new.jpg')..writeAsBytesSync(List.filled(80, 9));
    await store.importImage(d, 'back', src);
    d.status = DraftStatus.pendingUpload;
    await store.save(d);
    await sync.syncAll();
    expect(server.uploads, 3);
  });

  test('connectivity restoration triggers sync', () async {
    SharedPreferences.setMockInitialValues({});
    await queued(back: false);
    final conn = StreamController<bool>();
    final state = AppState(
      prefs: await SharedPreferences.getInstance(),
      api: HttpOcrApi(baseUrl: 'http://unused.invalid', tokens: MemoryTokenStore()),
      store: store,
      sync: sync,
      connectivity: conn.stream,
    );
    conn.add(false);
    await Future<void>.delayed(Duration.zero);
    expect(state.online, isFalse);
    expect(server.creates, 0);
    conn.add(true);
    for (var i = 0; i < 50 && store.all.single.status != DraftStatus.completed; i++) {
      await Future<void>.delayed(const Duration(milliseconds: 10));
    }
    expect(state.online, isTrue);
    expect(store.all.single.status, DraftStatus.completed);
    await conn.close();
    state.dispose();
  });
}
