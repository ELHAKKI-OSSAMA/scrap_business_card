import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _server = TextEditingController(text: context.read<AppState>().serverUrl);
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _error;
  bool _busy = false;

  Future<void> _auth({required bool register}) async {
    final l = AppLocalizations.of(context);
    setState(() { _busy = true; _error = null; });
    try {
      await context.read<AppState>().signIn(_email.text.trim(), _password.text, register: register);
      _password.clear();
    } on NetworkException {
      _error = l.errorNetwork;
    } on ApiException catch (e) {
      _error = e.status == 401 ? l.errorAuth : e.message;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = context.watch<AppState>();
    return Scaffold(
      appBar: AppBar(title: Text(l.settings)),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        DropdownButtonFormField<String?>(
          initialValue: state.locale?.languageCode,
          decoration: InputDecoration(labelText: l.language, border: const OutlineInputBorder()),
          items: const [
            DropdownMenuItem(value: null, child: Text('System')),
            DropdownMenuItem(value: 'en', child: Text('English')),
            DropdownMenuItem(value: 'fr', child: Text('Français')),
            DropdownMenuItem(value: 'ar', child: Text('العربية')),
          ],
          onChanged: (v) => state.setLocale(v),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _server,
          keyboardType: TextInputType.url,
          textDirection: TextDirection.ltr,
          decoration: InputDecoration(labelText: l.server, border: const OutlineInputBorder()),
          onSubmitted: state.setServer,
        ),
        const Divider(height: 32),
        if (state.signedInEmail != null) ...[
          Text(l.signedInAs(state.signedInEmail!)),
          const SizedBox(height: 8),
          OutlinedButton(onPressed: state.signOut, child: Text(l.signOut)),
        ] else ...[
          TextField(controller: _email, keyboardType: TextInputType.emailAddress, textDirection: TextDirection.ltr, autofillHints: const [AutofillHints.email],
              decoration: InputDecoration(labelText: l.email, border: const OutlineInputBorder())),
          const SizedBox(height: 8),
          TextField(controller: _password, obscureText: true, textDirection: TextDirection.ltr, autofillHints: const [AutofillHints.password],
              decoration: InputDecoration(labelText: l.password, border: const OutlineInputBorder())),
          if (_error != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: FilledButton(onPressed: _busy ? null : () async { await state.setServer(_server.text); await _auth(register: false); }, child: Text(l.signIn))),
            const SizedBox(width: 8),
            Expanded(child: OutlinedButton(onPressed: _busy ? null : () async { await state.setServer(_server.text); await _auth(register: true); }, child: Text(l.register))),
          ]),
        ],
        const Divider(height: 32),
        Text(l.offlineOcrNote, style: Theme.of(context).textTheme.bodySmall),
      ]),
    );
  }
}
