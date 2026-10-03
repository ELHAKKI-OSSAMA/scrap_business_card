import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api/api_client.dart';
import 'drafts/draft.dart';
import 'drafts/draft_store.dart';
import 'sync/sync_service.dart';

class SecureTokenStore implements TokenStore {
  static const _key = 'refresh_token';
  final _s = const FlutterSecureStorage();
  @override
  Future<String?> read() => _s.read(key: _key);
  @override
  Future<void> write(String? token) => token == null ? _s.delete(key: _key) : _s.write(key: _key, value: token);
}

/// App-wide state: language, server URL, session, connectivity and the sync engine.
class AppState extends ChangeNotifier {
  AppState({required this.prefs, required this.api, required this.store, required this.sync, Stream<bool>? connectivity}) {
    _locale = _parseLocale(prefs.getString('locale'));
    sync.onDocumentDone = () => unawaited(loadDocs());
    _sub = (connectivity ?? _connectivityStream()).listen((up) {
      final was = online;
      online = up;
      notifyListeners();
      if (up && !was) unawaited(sync.syncAll()); // reconnect -> flush the queue
    });
  }

  final SharedPreferences prefs;
  final HttpOcrApi api;
  final DraftStore store;
  final SyncService sync;
  StreamSubscription<bool>? _sub;
  bool online = true;
  Locale? _locale;
  String? signedInEmail;
  String? displayName;

  /// True until the stored session has been checked at start-up (splash screen).
  bool restoring = true;

  /// Server documents (source of truth); null until first loaded.
  List<DocSummary>? docs;
  bool loadingDocs = false;
  String? docsError;

  static const defaultServer = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8080/api/v1');

  Locale? get locale => _locale;
  String get serverUrl => prefs.getString('server') ?? defaultServer;

  static Stream<bool> _connectivityStream() =>
      Connectivity().onConnectivityChanged.map((r) => r.any((c) => c != ConnectivityResult.none));

  static Locale? _parseLocale(String? code) => code == null || code.isEmpty ? null : Locale(code);

  Future<void> setLocale(String? code) async {
    _locale = _parseLocale(code);
    if (code == null) {
      await prefs.remove('locale');
    } else {
      await prefs.setString('locale', code);
    }
    notifyListeners();
  }

  Future<void> setServer(String url) async {
    await prefs.setString('server', url.trim());
    api.baseUrl = url.trim();
    notifyListeners();
  }

  Future<void> restoreSession() async {
    try {
      if (await api.refresh()) {
        final me = await api.me();
        signedInEmail = me['email'] as String?;
        displayName = me['display_name'] as String?;
        unawaited(refreshAll());
      }
    } on NetworkException {
      online = false;
      // offline start: keep the user in if a session exists locally
      if (await api.tokens.read() != null) signedInEmail = '';
    } on ApiException {
      signedInEmail = null;
    } finally {
      restoring = false;
      notifyListeners();
    }
  }

  /// Sends queued scans, then reloads the server list.
  Future<void> refreshAll() async {
    await sync.syncAll();
    await loadDocs();
  }

  /// Reloads the server list and removes local copies of cards deleted elsewhere (web).
  Future<void> loadDocs() async {
    if (signedInEmail == null) return;
    loadingDocs = true;
    notifyListeners();
    try {
      final list = await api.listDocuments('business-cards');
      docs = list;
      docsError = null;
      final ids = list.map((d) => d.id).toSet();
      for (final d in [...store.all]) {
        final finished = d.status == DraftStatus.completed || d.status == DraftStatus.failed;
        if (finished && d.serverId != null && !ids.contains(d.serverId)) await store.delete(d);
      }
    } on NetworkException {
      docsError = 'network';
    } on ApiException catch (e) {
      docsError = e.message;
      if (e.isAuth) signedInEmail = null;
    } finally {
      loadingDocs = false;
      notifyListeners();
    }
  }

  Future<void> deleteDocument(String id) async {
    await api.deleteDocument('business-cards', id);
    docs = docs?.where((d) => d.id != id).toList();
    for (final d in [...store.all]) {
      if (d.serverId == id) await store.delete(d);
    }
    notifyListeners();
  }

  Future<void> signIn(String email, String password, {bool register = false}) async {
    if (register) {
      await api.register(email, password, _locale?.languageCode ?? 'en');
    } else {
      await api.login(email, password);
    }
    signedInEmail = email;
    try {
      displayName = (await api.me())['display_name'] as String?;
    } catch (_) {}
    notifyListeners();
    unawaited(refreshAll());
  }

  Future<void> signOut() async {
    await api.logout();
    signedInEmail = null;
    displayName = null;
    docs = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
