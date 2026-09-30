import 'dart:io';

import 'package:ocr_suite_mobile/src/api/api_client.dart';

/// In-memory server double enforcing the real API's idempotency rules
/// (UNIQUE client_ref; process returns a job). It produces no OCR content of its own:
/// `resultData` is whatever the test sets explicitly.
class FakeServer implements OcrApi {
  bool offline = false;
  int failUploadsAfter = -1; // simulate a connection drop mid-batch
  final docs = <String, Map<String, dynamic>>{}; // clientRef -> doc
  int creates = 0, uploads = 0, processes = 0, patches = 0;
  String jobStatus = 'completed';
  Map<String, dynamic> resultData = {};

  void _net() {
    if (offline) throw NetworkException('offline');
  }

  @override
  Future<RemoteDoc> createDocument(String route, {required String clientRef, String? title}) async {
    _net();
    creates++;
    final d = docs.putIfAbsent(clientRef, () => {'id': 'doc-${docs.length + 1}', 'status': 'draft', 'version': 1, 'data': null});
    return RemoteDoc(d);
  }

  @override
  Future<RemoteDoc> uploadImage(String route, String id, String side, File file, {void Function(int percent)? onProgress}) async {
    _net();
    if (failUploadsAfter >= 0 && uploads >= failUploadsAfter) throw NetworkException('dropped');
    uploads++;
    onProgress?.call(100);
    return RemoteDoc(docs.values.firstWhere((d) => d['id'] == id));
  }

  @override
  Future<JobStatus> process(String route, String id) async {
    _net();
    processes++;
    return JobStatus('job-$id', 'queued');
  }

  @override
  Future<JobStatus> job(String jobId) async {
    _net();
    return JobStatus(jobId, jobStatus, errorCode: jobStatus == 'failed' ? 'ocr_error' : null);
  }

  @override
  Future<RemoteDoc> getDocument(String route, String id) async {
    _net();
    return RemoteDoc({'id': id, 'status': 'completed', 'version': 2, 'data': resultData});
  }

  @override
  Future<RemoteDoc> patchField(String route, String id, String path, Object? value, {int? expectedVersion}) async {
    _net();
    patches++;
    resultData = {...resultData, path: {'value': value, 'confidence': 1.0, 'review_status': 'user_edited'}};
    return RemoteDoc({'id': id, 'status': 'completed', 'version': 3, 'data': resultData});
  }
}
