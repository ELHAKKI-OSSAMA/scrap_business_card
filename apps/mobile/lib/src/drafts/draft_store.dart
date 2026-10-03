import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;

import 'draft.dart';

/// Drafts are stored as JSON plus image files inside the app's private documents directory
/// (sandboxed per app on Android/iOS; iOS applies Data Protection, Android app storage is not
/// readable by other apps). Writes are atomic (temp file + rename) so an interrupted save never
/// corrupts the queue.
class DraftStore extends ChangeNotifier {
  DraftStore(this.root);

  final Directory root;
  final List<Draft> _drafts = [];
  bool _loaded = false;

  File get _index => File(p.join(root.path, 'drafts.json'));

  Future<List<Draft>> load() async {
    if (_loaded) return List.unmodifiable(_drafts);
    await root.create(recursive: true);
    if (await _index.exists()) {
      final raw = jsonDecode(await _index.readAsString()) as List<dynamic>;
      _drafts
        ..clear()
        ..addAll(raw.map((e) => Draft.fromJson(e as Map<String, dynamic>)));
    }
    _loaded = true;
    return List.unmodifiable(_drafts);
  }

  List<Draft> get all => List.unmodifiable(_drafts..sort((a, b) => b.updatedAt.compareTo(a.updatedAt)));

  Draft? byId(String id) => _drafts.where((d) => d.localId == id).firstOrNull;

  Future<void> _pending = Future.value();

  /// Writes are serialised: two overlapping saves (sync + UI) must not race on the temp file.
  Future<void> _flush() {
    final next = _pending.then((_) => _write(), onError: (_) => _write());
    _pending = next.catchError((_) {});
    return next;
  }

  Future<void> _write() async {
    final tmp = File('${_index.path}.tmp');
    await tmp.writeAsString(jsonEncode(_drafts.map((d) => d.toJson()).toList()), flush: true);
    for (var i = 0; ; i++) {
      try {
        await tmp.rename(_index.path);
        return;
      } on FileSystemException {
        if (i >= 5) rethrow; // Windows can hold the target briefly (indexer / antivirus)
        await Future<void>.delayed(Duration(milliseconds: 20 * (i + 1)));
      }
    }
  }

  Future<Draft> save(Draft d) async {
    await load();
    d.touch();
    final i = _drafts.indexWhere((x) => x.localId == d.localId);
    if (i >= 0) {
      _drafts[i] = d;
    } else {
      _drafts.add(d);
    }
    await _flush();
    notifyListeners();
    return d;
  }

  /// Copies a captured image into private storage (picker/camera files are temporary).
  Future<String> importImage(Draft d, String side, File source) async {
    final dir = Directory(p.join(root.path, 'images', d.localId));
    await dir.create(recursive: true);
    final dest = File(p.join(dir.path, '$side-${DateTime.now().millisecondsSinceEpoch}${p.extension(source.path).isEmpty ? '.jpg' : p.extension(source.path)}'));
    await source.copy(dest.path);
    final old = d.images[side];
    if (old != null && old != dest.path) {
      try {
        await File(old).delete();
      } catch (_) {}
    }
    d.images[side] = dest.path;
    return dest.path;
  }

  Future<void> removeImage(Draft d, String side) async {
    final path = d.images.remove(side);
    d.uploadedSha.remove(side);
    if (path != null) {
      try {
        await File(path).delete();
      } catch (_) {}
    }
  }

  Future<void> delete(Draft d) async {
    await load();
    _drafts.removeWhere((x) => x.localId == d.localId);
    final dir = Directory(p.join(root.path, 'images', d.localId));
    if (await dir.exists()) await dir.delete(recursive: true);
    await _flush();
    notifyListeners();
  }
}
