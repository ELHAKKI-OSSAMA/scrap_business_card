import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'l10n/gen/app_localizations.dart';
import 'src/api/api_client.dart';
import 'src/app_state.dart';
import 'src/drafts/draft_store.dart';
import 'src/sync/sync_service.dart';
import 'src/ui/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final docs = await getApplicationDocumentsDirectory();
  final store = DraftStore(Directory(p.join(docs.path, 'ocr_drafts')));
  await store.load();
  final api = HttpOcrApi(baseUrl: prefs.getString('server') ?? AppState.defaultServer, tokens: SecureTokenStore());
  final sync = SyncService(store: store, api: api);
  final state = AppState(prefs: prefs, api: api, store: store, sync: sync);
  state.restoreSession();
  runApp(OcrApp(state: state));
}

class OcrApp extends StatelessWidget {
  const OcrApp({super.key, required this.state});
  final AppState state;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: state),
        ChangeNotifierProvider.value(value: state.sync),
        ChangeNotifierProvider.value(value: state.store),
      ],
      child: Consumer<AppState>(
        builder: (context, s, _) => MaterialApp(
          onGenerateTitle: (c) => AppLocalizations.of(c).appTitle,
          locale: s.locale,
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          theme: ThemeData(colorSchemeSeed: const Color(0xFF1F4FD8), useMaterial3: true, brightness: Brightness.light),
          darkTheme: ThemeData(colorSchemeSeed: const Color(0xFF1F4FD8), useMaterial3: true, brightness: Brightness.dark),
          home: const HomeScreen(),
        ),
      ),
    );
  }
}
