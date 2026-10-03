import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// Thrown when the server cannot be reached (offline, DNS, timeout). Drafts stay queued.
class NetworkException implements Exception {
  NetworkException(this.message);
  final String message;
  @override
  String toString() => 'NetworkException: $message';
}

/// An error response from the API (`{"error": {"code", "message"}}`).
class ApiException implements Exception {
  ApiException(this.status, this.code, this.message);
  final int status;
  final String code;
  final String message;
  bool get isAuth => status == 401;
  @override
  String toString() => 'ApiException($status, $code): $message';
}

class RemoteDoc {
  RemoteDoc(this.json);
  final Map<String, dynamic> json;
  String get id => json['id'] as String;
  String get status => json['status'] as String;
  int get version => json['version'] as int;
  Map<String, dynamic>? get data => json['data'] as Map<String, dynamic>?;
}

/// One row of the server list (`GET /{route}`): the source of truth for what exists.
class DocSummary {
  DocSummary(this.json);
  final Map<String, dynamic> json;
  String get id => json['id'] as String;
  String? get title => json['title'] as String?;
  String get status => json['status'] as String? ?? 'draft';
  String get reviewStatus => json['review_status'] as String? ?? 'unreviewed';
  bool get favorite => json['favorite'] as bool? ?? false;
  Map<String, dynamic> get summary => (json['summary'] as Map?)?.cast<String, dynamic>() ?? const {};
  DateTime get updatedAt => DateTime.tryParse(json['updated_at'] as String? ?? '') ?? DateTime.now();
  String? s(String k) => (summary[k] as String?)?.trim().isEmpty ?? true ? null : (summary[k] as String).trim();
  String get displayName => s('full_name') ?? s('arabic_name') ?? title ?? s('company') ?? '—';
  String get searchText => [title, ...summary.values.whereType<String>()].whereType<String>().join(' ').toLowerCase();
}

class JobStatus {
  JobStatus(this.id, this.status, {this.errorCode, this.errorMessage});
  final String id;
  final String status; // queued | running | completed | failed
  final String? errorCode;
  final String? errorMessage;
}

/// Persists the refresh token (flutter_secure_storage in the app, in-memory in tests).
abstract class TokenStore {
  Future<String?> read();
  Future<void> write(String? token);
}

class MemoryTokenStore implements TokenStore {
  String? _v;
  @override
  Future<String?> read() async => _v;
  @override
  Future<void> write(String? token) async => _v = token;
}

/// Interface used by the sync engine (and faked in tests).
abstract class OcrApi {
  Future<RemoteDoc> createDocument(String route, {required String clientRef, String? title});
  Future<RemoteDoc> uploadImage(String route, String id, String side, File file, {void Function(int percent)? onProgress});
  Future<JobStatus> process(String route, String id);
  Future<JobStatus> job(String jobId);
  Future<RemoteDoc> getDocument(String route, String id);
  Future<RemoteDoc> patchField(String route, String id, String path, Object? value, {int? expectedVersion});
}

class HttpOcrApi implements OcrApi {
  HttpOcrApi({required this.baseUrl, required this.tokens, http.Client? client, this.timeout = const Duration(seconds: 60)})
      : _client = client ?? http.Client();

  String baseUrl; // e.g. http://10.0.2.2:8080/api/v1
  final TokenStore tokens;
  final http.Client _client;
  final Duration timeout;
  String? _access;
  String? email;

  bool get hasAccessToken => _access != null;

  Uri _u(String path) => Uri.parse('${baseUrl.replaceAll(RegExp(r'/+$'), '')}$path');

  Future<http.Response> _send(Future<http.Response> Function() call) async {
    try {
      return await call().timeout(timeout);
    } on SocketException catch (e) {
      throw NetworkException(e.message);
    } on TimeoutException {
      throw NetworkException('timeout');
    } on http.ClientException catch (e) {
      throw NetworkException(e.message);
    } on HandshakeException catch (e) {
      throw NetworkException(e.message);
    }
  }

  Never _error(http.Response r) {
    String code = 'http_error';
    String message = r.reasonPhrase ?? 'HTTP ${r.statusCode}';
    try {
      final body = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
      final err = body['error'] as Map<String, dynamic>?;
      code = err?['code'] as String? ?? code;
      message = err?['message'] as String? ?? message;
    } catch (_) {}
    throw ApiException(r.statusCode, code, message);
  }

  Map<String, dynamic> _json(http.Response r) => jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;

  Future<void> _storeTokens(Map<String, dynamic> t) async {
    _access = t['access_token'] as String;
    await tokens.write(t['refresh_token'] as String);
  }

  Future<void> login(String email, String password) async {
    final r = await _send(() => _client.post(_u('/auth/login'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'email': email, 'password': password})));
    if (r.statusCode != 200) _error(r);
    await _storeTokens(_json(r));
    this.email = email;
  }

  Future<void> register(String email, String password, String locale) async {
    final r = await _send(() => _client.post(_u('/auth/register'), headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password, 'locale': locale})));
    if (r.statusCode != 201) _error(r);
    await _storeTokens(_json(r));
    this.email = email;
  }

  Future<bool> refresh() async {
    final rt = await tokens.read();
    if (rt == null) return false;
    final r = await _send(() => _client.post(_u('/auth/refresh'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'refresh_token': rt})));
    if (r.statusCode != 200) {
      if (r.statusCode == 401) await tokens.write(null);
      return false;
    }
    await _storeTokens(_json(r));
    return true;
  }

  Future<void> logout() async {
    final rt = await tokens.read();
    _access = null;
    await tokens.write(null);
    if (rt != null) {
      try {
        await _client.post(_u('/auth/logout'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'refresh_token': rt})).timeout(const Duration(seconds: 5));
      } catch (_) {}
    }
  }

  /// All documents of the workspace (newest first), up to [max].
  Future<List<DocSummary>> listDocuments(String route, {int max = 500}) async {
    final out = <DocSummary>[];
    for (var page = 1; out.length < max; page++) {
      final j = _json(await _authed((h) => _client.get(_u('/$route?page=$page&page_size=100&sort=updated_desc'), headers: h)));
      final items = (j['items'] as List).cast<Map<String, dynamic>>().map(DocSummary.new).toList();
      out.addAll(items);
      if (items.length < 100 || out.length >= (j['total'] as int)) break;
    }
    return out;
  }

  Future<void> deleteDocument(String route, String id) async {
    await _authed((h) => _client.delete(_u('/$route/$id'), headers: h));
  }

  /// Is self-registration open on this server? (`GET /auth/config`; old servers: assume yes)
  Future<bool> registrationOpen() async {
    try {
      final r = await _send(() => _client.get(_u('/auth/config')));
      if (r.statusCode != 200) return true;
      return _json(r)['registration_open'] as bool? ?? true;
    } on NetworkException {
      return false;
    }
  }

  Future<Map<String, dynamic>> me() async => _json(await _authed((h) => _client.get(_u('/me'), headers: h)));

  Future<http.Response> _authed(Future<http.Response> Function(Map<String, String> headers) call, {bool retry = true}) async {
    if (_access == null) await refresh();
    final headers = {'Content-Type': 'application/json', if (_access != null) 'Authorization': 'Bearer $_access'};
    final r = await _send(() => call(headers));
    if (r.statusCode == 401 && retry && await refresh()) return _authed(call, retry: false);
    if (r.statusCode >= 400) _error(r);
    return r;
  }

  @override
  Future<RemoteDoc> createDocument(String route, {required String clientRef, String? title}) async {
    final r = await _authed((h) => _client.post(_u('/$route'), headers: h, body: jsonEncode({'client_ref': clientRef, if (title != null && title.isNotEmpty) 'title': title})));
    return RemoteDoc(_json(r));
  }

  @override
  Future<RemoteDoc> uploadImage(String route, String id, String side, File file, {void Function(int percent)? onProgress}) async {
    Future<http.Response> doUpload() async {
      if (_access == null) await refresh();
      final total = await file.length();
      var sent = 0;
      final stream = file.openRead().transform(StreamTransformer<List<int>, List<int>>.fromHandlers(handleData: (chunk, sink) {
        sent += chunk.length;
        onProgress?.call(total == 0 ? 100 : (sent * 100 ~/ total));
        sink.add(chunk);
      }));
      final req = http.MultipartRequest('POST', _u('/$route/$id/images?side=$side'))
        ..headers.addAll({if (_access != null) 'Authorization': 'Bearer $_access'})
        ..files.add(http.MultipartFile('file', stream, total, filename: '$side.jpg'));
      return http.Response.fromStream(await _client.send(req));
    }

    var r = await _send(doUpload);
    if (r.statusCode == 401 && await refresh()) r = await _send(doUpload);
    if (r.statusCode >= 400) _error(r);
    return RemoteDoc(_json(r));
  }

  @override
  Future<JobStatus> process(String route, String id) async {
    final r = await _authed((h) => _client.post(_u('/$route/$id/process'), headers: h, body: '{}'));
    final j = _json(r);
    return JobStatus(j['job_id'] as String, j['status'] as String);
  }

  @override
  Future<JobStatus> job(String jobId) async {
    final j = _json(await _authed((h) => _client.get(_u('/jobs/$jobId'), headers: h)));
    return JobStatus(j['id'] as String, j['status'] as String, errorCode: j['error_code'] as String?, errorMessage: j['error_message'] as String?);
  }

  @override
  Future<RemoteDoc> getDocument(String route, String id) async => RemoteDoc(_json(await _authed((h) => _client.get(_u('/$route/$id'), headers: h))));

  @override
  Future<RemoteDoc> patchField(String route, String id, String path, Object? value, {int? expectedVersion}) async {
    final body = {'changes': [{'path': path, 'value': value}], 'expected_version': ?expectedVersion};
    return RemoteDoc(_json(await _authed((h) => _client.patch(_u('/$route/$id/fields'), headers: h, body: jsonEncode(body)))));
  }
}
