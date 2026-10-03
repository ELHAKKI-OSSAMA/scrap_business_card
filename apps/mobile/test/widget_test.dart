import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ocr_suite_mobile/l10n/gen/app_localizations.dart';
import 'package:ocr_suite_mobile/main.dart';
import 'package:ocr_suite_mobile/src/api/api_client.dart';
import 'package:ocr_suite_mobile/src/app_state.dart';
import 'package:ocr_suite_mobile/src/drafts/draft.dart';
import 'package:ocr_suite_mobile/src/drafts/draft_store.dart';
import 'package:ocr_suite_mobile/src/modules/product.dart';
import 'package:ocr_suite_mobile/src/sync/sync_service.dart';
import 'package:ocr_suite_mobile/src/ui/review_screen.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fakes.dart';

late Directory tmp;
late DraftStore store;
late StreamController<bool> conn;

Future<AppState> makeState({String? locale, bool signedIn = true}) async {
  SharedPreferences.setMockInitialValues(locale == null ? {} : {'locale': locale});
  store = DraftStore(Directory('${tmp.path}/drafts'));
  await store.load();
  conn = StreamController<bool>.broadcast();
  final server = FakeServer()..offline = true; // widget tests never touch a network
  final s = AppState(
    prefs: await SharedPreferences.getInstance(),
    api: HttpOcrApi(baseUrl: 'http://unused.invalid', tokens: MemoryTokenStore()),
    store: store,
    sync: SyncService(store: store, api: server, pollInterval: Duration.zero, maxPolls: 1),
    connectivity: conn.stream,
  );
  s.restoring = false;
  if (signedIn) {
    s.signedInEmail = 'tester@example.com';
    s.docs = []; // server list already loaded (empty); widget tests never touch a network
  }
  return s;
}

AppLocalizations l10n(String code) => lookupAppLocalizations(Locale(code));

void main() {
  setUp(() async => tmp = await Directory.systemTemp.createTemp('ocr_widget_test'));
  tearDown(() async {
    await conn.close();
    await tmp.delete(recursive: true);
  });

  testWidgets('home opens the business-card module with the empty state (English)', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'en'));
    await t.pumpWidget(OcrApp(state: s!));
    await t.pumpAndSettle();
    final l = l10n('en');
    expect(find.text(l.cardScanner), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.text(l.emptyTitle), findsOneWidget);
    expect(find.text(l.scanCard), findsOneWidget);
  });

  testWidgets('the login screen is shown before the app when nobody is signed in', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'fr', signedIn: false));
    await t.pumpWidget(OcrApp(state: s!));
    await t.pumpAndSettle();
    final l = l10n('fr');
    expect(find.text(l.welcome), findsOneWidget);
    expect(find.byKey(const Key('login-email')), findsOneWidget);
    expect(find.byKey(const Key('login-submit')), findsOneWidget);
    expect(find.text(l.scanCard), findsNothing);
  });

  testWidgets('cards from the server are listed, including those created on the web', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'en'));
    s!.docs = [
      DocSummary({'id': '1', 'title': null, 'status': 'completed', 'review_status': 'needs_review', 'favorite': true, 'summary': {'full_name': 'Mahmoud ATIF', 'job_title': 'Directeur', 'company': 'OMNISHORE', 'email': 'm@x.ma'}, 'updated_at': '2026-10-02T10:00:00Z'}),
      DocSummary({'id': '2', 'title': null, 'status': 'completed', 'review_status': 'unreviewed', 'summary': {'full_name': 'Jane Roe'}, 'updated_at': '2026-10-01T10:00:00Z'}),
    ];
    await t.pumpWidget(OcrApp(state: s));
    await t.pumpAndSettle();
    final l = l10n('en');
    expect(find.text('Mahmoud ATIF'), findsOneWidget);
    expect(find.text('Directeur · OMNISHORE'), findsOneWidget);
    expect(find.text('Jane Roe'), findsOneWidget);
    expect(find.text(l.needsReview), findsOneWidget);
    await t.enterText(find.byType(TextField), 'omni');
    await t.pumpAndSettle();
    expect(find.text('Jane Roe'), findsNothing);
  });

  testWidgets('French UI is left-to-right', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'fr'));
    await t.pumpWidget(OcrApp(state: s!));
    await t.pumpAndSettle();
    expect(find.text(l10n('fr').cardScanner), findsOneWidget);
    expect(Directionality.of(t.element(find.byType(Scaffold).first)), TextDirection.ltr);
  });

  testWidgets('Arabic UI is right-to-left with Arabic strings', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'ar'));
    await t.pumpWidget(OcrApp(state: s!));
    await t.pumpAndSettle();
    final l = l10n('ar');
    expect(find.text(l.cardScanner), findsOneWidget);
    expect(Directionality.of(t.element(find.byType(Scaffold).first)), TextDirection.rtl);
    // FAB sits at the end edge: on the left in RTL.
    final fab = t.getCenter(find.byType(FloatingActionButton));
    expect(fab.dx, lessThan(t.view.physicalSize.width / t.view.devicePixelRatio / 2));
  });

  testWidgets('offline banner appears when connectivity drops', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'en'));
    await t.pumpWidget(OcrApp(state: s!));
    conn.add(false);
    await t.pumpAndSettle();
    expect(find.text(l10n('en').offlineBanner), findsOneWidget);
    await t.runAsync(() async {
      conn.add(true);
      await Future<void>.delayed(const Duration(milliseconds: 200)); // reconnect sync runs on real IO
    });
    await t.pump();
    expect(find.text(l10n('en').offlineBanner), findsNothing);
  });

  testWidgets('pending list shows local, pending and failed scans (completed ones come from the server) and search filters', (t) async {
    final s = await t.runAsync(() async {
      final s = await makeState(locale: 'en');
      await store.save(Draft(localId: 'a', product: 'business_card', title: 'Alpha'));
      await store.save(Draft(localId: 'b', product: 'business_card', title: 'Bravo', status: DraftStatus.pendingUpload));
      await store.save(Draft(localId: 'c', product: 'business_card', title: 'Charlie', status: DraftStatus.failed, error: 'ocr_error'));
      await store.save(Draft(localId: 'd', product: 'business_card', title: 'Delta', status: DraftStatus.completed));
      return s;
    });
    await t.pumpWidget(OcrApp(state: s!));
    await t.pumpAndSettle();
    final l = l10n('en');
    for (final label in [l.statusLocalDraft, l.statusPendingUpload, l.statusFailed]) {
      expect(find.text(label), findsOneWidget);
    }
    expect(find.text('Delta'), findsNothing); // completed: shown from the server list
    await t.enterText(find.byType(TextField), 'char');
    await t.pumpAndSettle();
    expect(find.text('Charlie'), findsOneWidget);
    expect(find.text('Alpha'), findsNothing);
  });

  testWidgets('capture: submit without a front image is refused; save draft persists the title', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'en'));
    await t.pumpWidget(OcrApp(state: s!));
    await t.pumpAndSettle();
    final l = l10n('en');
    await t.tap(find.byType(FloatingActionButton));
    await t.pumpAndSettle();
    expect(find.text(l.scanDocument), findsNWidgets(2)); // front + back
    await t.tap(find.text(l.submit));
    await t.pump();
    expect(find.text(l.needImage), findsOneWidget);
    await t.enterText(find.widgetWithText(TextField, l.title), 'Grandma');
    await t.runAsync(() async {
      await t.tap(find.text(l.saveDraft));
      await Future<void>.delayed(const Duration(milliseconds: 100));
    });
    await t.pumpAndSettle();
    expect(store.all.single.title, 'Grandma');
    expect(store.all.single.status, DraftStatus.localDraft);
    expect(find.text('Grandma'), findsOneWidget);
  });

  testWidgets('review shows values, confidence, needs-review and not-found; Arabic value is RTL', (t) async {
    final s = await t.runAsync(() => makeState(locale: 'en'));
    final d = Draft(localId: 'r', product: 'business_card', status: DraftStatus.completed, result: {
      'full_name': {'value': 'Jane Roe', 'confidence': 0.91, 'review_status': 'auto'},
      'arabic_name': {'value': 'سارة', 'confidence': 0.42, 'review_status': 'needs_review'},
      'job_title': null,
      'phones': [{'original': '+212 600 000 000', 'type': 'mobile', 'e164': '+212600000000'}],
      'emails': [{'value': 'jane@example.com'}],
    });
    t.view.physicalSize = const Size(1200, 5000);
    t.view.devicePixelRatio = 1;
    addTearDown(t.view.reset);
    await t.pumpWidget(ChangeNotifierProvider<AppState>.value(
      value: s!,
      child: MaterialApp(
        locale: const Locale('en'),
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: ReviewScreen(draft: d),
      ),
    ));
    await t.pumpAndSettle();
    final l = l10n('en');
    expect(find.text('Jane Roe'), findsWidgets); // header + field
    expect(find.text(l.confidence(91)), findsOneWidget);
    expect(find.text(l.needsReview), findsOneWidget);
    expect(find.text(l.notFound), findsWidgets);
    expect(t.widget<Text>(find.text('سارة')).textDirection, TextDirection.rtl);
    // Not uploaded (no serverId): editing is disabled rather than silently lost.
    expect(t.widget<IconButton>(find.widgetWithIcon(IconButton, Icons.edit_outlined).first).onPressed, isNull);
    await t.scrollUntilVisible(find.text('jane@example.com'), 200);
    expect(find.text('jane@example.com'), findsOneWidget);
    expect(ProductModule.businessCard.fields.length, greaterThan(0));
  });

  test('all three locales define every key', () {
    for (final code in ['en', 'fr', 'ar']) {
      final l = l10n(code);
      expect(l.appTitle, isNotEmpty);
      expect(l.cardScanner, isNotEmpty);
      expect(l.offlineOcrNote, isNotEmpty);
    }
    expect(l10n('ar').cardScanner, isNot(l10n('en').cardScanner));
    expect(l10n('fr').cardScanner, isNot(l10n('en').cardScanner));
  });
}
