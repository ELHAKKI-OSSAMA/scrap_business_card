import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api/api_client.dart';
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
        signedInEmail = (await api.me())['email'] as String?;
        notifyListeners();
      }
    } on NetworkException {
      online = false;
      notifyListeners();
    }
  }

  Future<void> signIn(String email, String password, {bool register = false}) async {
    if (register) {
      await api.register(email, password, _locale?.languageCode ?? 'en');
    } else {
      await api.login(email, password);
    }
    signedInEmail = email;
    notifyListeners();
    unawaited(sync.syncAll());
  }

  Future<void> signOut() async {
    await api.logout();
    signedInEmail = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
