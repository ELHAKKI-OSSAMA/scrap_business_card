import 'dart:async';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';
import '../drafts/draft.dart';
import '../drafts/draft_store.dart';
import '../modules/product.dart';

/// Uploads queued drafts and follows their server jobs.
///
/// Idempotency (no duplicates after reconnects or interrupted uploads):
///  * the document is created with `client_ref = draft.localId`; the server returns the existing
///    document on replay (UNIQUE(workspace, client_ref));
///  * each side's sha256 is remembered after a successful upload and not sent again; the server
///    also treats a same-hash re-upload as a no-op;
///  * `process` with unchanged images returns the existing job (server-side input hash).
class SyncService extends ChangeNotifier {
  SyncService({required this.store, required this.api, this.pollInterval = const Duration(seconds: 2), this.maxPolls = 90});

  final DraftStore store;
  final OcrApi api;
  final Duration pollInterval;
  final int maxPolls;
  bool _running = false;
  final Map<String, int> progress = {}; // localId -> upload percent
  String? lastError;

  bool get running => _running;

  static Future<String> sha256File(File f) async => (await sha256.bind(f.openRead()).first).toString();

  /// Returns true when the queue was fully processed, false if it stopped (offline / auth).
  Future<bool> syncAll() async {
    if (_running) return false;
    _running = true;
    lastError = null;
    notifyListeners();
    try {
      await store.load();
      for (final d in store.all.where((d) => d.status == DraftStatus.pendingUpload || d.status == DraftStatus.processing).toList()) {
        final ok = await syncOne(d);
        if (!ok) return false;
      }
      return true;
    } finally {
      _running = false;
      notifyListeners();
    }
  }

  Future<bool> syncOne(Draft d) async {
    final module = ProductModule.byKey(d.product);
    try {
      if (d.status == DraftStatus.pendingUpload) {
        if (d.serverId == null) {
          final doc = await api.createDocument(module.route, clientRef: d.localId, title: d.title);
          d.serverId = doc.id;
          await store.save(d);
        }
        for (final entry in d.images.entries) {
          final file = File(entry.value);
          final hash = await sha256File(file);
          if (d.uploadedSha[entry.key] == hash) continue;
          await api.uploadImage(module.route, d.serverId!, entry.key, file, onProgress: (pct) {
            progress[d.localId] = pct;
            notifyListeners();
          });
          d.uploadedSha[entry.key] = hash;
          await store.save(d); // persisted per side: an interrupted batch resumes where it stopped
        }
        progress.remove(d.localId);
        final job = await api.process(module.route, d.serverId!);
        d.jobId = job.id;
        d.status = DraftStatus.processing;
        d.error = null;
        await store.save(d);
        notifyListeners();
      }
      if (d.status == DraftStatus.processing && d.jobId != null) {
        for (var i = 0; i < maxPolls; i++) {
          final j = await api.job(d.jobId!);
          if (j.status == 'completed') {
            final doc = await api.getDocument(module.route, d.serverId!);
            d.result = doc.data;
            d.status = DraftStatus.completed;
            await store.save(d);
            notifyListeners();
            return true;
          }
          if (j.status == 'failed') {
            d.status = DraftStatus.failed;
            d.error = j.errorCode ?? 'processing_error';
            await store.save(d);
            notifyListeners();
            return true;
          }
          await Future<void>.delayed(pollInterval);
        }
      }
      return true;
    } on NetworkException catch (e) {
      lastError = 'network: ${e.message}';
      progress.remove(d.localId);
      notifyListeners();
      return false; // stay queued; retried when connectivity returns
    } on ApiException catch (e) {
      progress.remove(d.localId);
      if (e.isAuth) {
        lastError = 'auth';
        notifyListeners();
        return false;
      }
      d.status = DraftStatus.failed;
      d.error = e.code;
      await store.save(d);
      notifyListeners();
      return true;
    }
  }

  /// Moves a failed draft back into the queue.
  Future<void> retry(Draft d) async {
    d.status = DraftStatus.pendingUpload; // already-uploaded sides are skipped by hash
    d.error = null;
    await store.save(d);
    notifyListeners();
  }
}
