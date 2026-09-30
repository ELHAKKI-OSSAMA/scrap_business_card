/// Local lifecycle of a scan. OCR never "completes" offline: `completed` is only set after the
/// server finished processing and the result was fetched.
enum DraftStatus { localDraft, pendingUpload, processing, completed, failed }

class Draft {
  Draft({
    required this.localId,
    required this.product,
    this.title,
    Map<String, String>? images,
    this.status = DraftStatus.localDraft,
    this.serverId,
    this.jobId,
    this.error,
    Map<String, String>? uploadedSha,
    this.result,
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : images = images ?? {},
        uploadedSha = uploadedSha ?? {},
        createdAt = createdAt ?? DateTime.now().toUtc(),
        updatedAt = updatedAt ?? DateTime.now().toUtc();

  /// Also used as the server `client_ref` idempotency key.
  final String localId;
  final String product; // business_card
  String? title;
  final Map<String, String> images; // side -> absolute path in app-private storage
  DraftStatus status;
  String? serverId;
  String? jobId;
  String? error;
  final Map<String, String> uploadedSha; // side -> sha256 already uploaded (skip re-uploads)
  Map<String, dynamic>? result; // extracted data fetched from the server
  final DateTime createdAt;
  DateTime updatedAt;

  void touch() => updatedAt = DateTime.now().toUtc();

  Map<String, dynamic> toJson() => {
        'localId': localId,
        'product': product,
        'title': title,
        'images': images,
        'status': status.name,
        'serverId': serverId,
        'jobId': jobId,
        'error': error,
        'uploadedSha': uploadedSha,
        'result': result,
        'createdAt': createdAt.toIso8601String(),
        'updatedAt': updatedAt.toIso8601String(),
      };

  factory Draft.fromJson(Map<String, dynamic> j) => Draft(
        localId: j['localId'] as String,
        product: j['product'] as String,
        title: j['title'] as String?,
        images: Map<String, String>.from(j['images'] as Map? ?? {}),
        status: DraftStatus.values.firstWhere((s) => s.name == j['status'], orElse: () => DraftStatus.localDraft),
        serverId: j['serverId'] as String?,
        jobId: j['jobId'] as String?,
        error: j['error'] as String?,
        uploadedSha: Map<String, String>.from(j['uploadedSha'] as Map? ?? {}),
        result: j['result'] as Map<String, dynamic>?,
        createdAt: DateTime.tryParse(j['createdAt'] as String? ?? ''),
        updatedAt: DateTime.tryParse(j['updatedAt'] as String? ?? ''),
      );

  /// Text used for local search (title + extracted values).
  String get searchText {
    final parts = <String>[title ?? ''];
    void walk(Object? o) {
      if (o is Map) {
        if (o['value'] != null) parts.add(o['value'].toString());
        o.values.forEach(walk);
      } else if (o is List) {
        o.forEach(walk);
      }
    }

    walk(result);
    return parts.join(' ').toLowerCase();
  }
}
