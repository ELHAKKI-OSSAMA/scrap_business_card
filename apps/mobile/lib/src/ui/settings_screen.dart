import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../app_state.dart';
import 'theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _server = TextEditingController(text: context.read<AppState>().serverUrl);

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = context.watch<AppState>();
    final theme = Theme.of(context);
    final who = (state.displayName?.isNotEmpty ?? false) ? state.displayName! : (state.signedInEmail ?? '');
    return Scaffold(
      appBar: AppBar(title: Text(l.settings)),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 4, 16, 24), children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(children: [
              InitialsAvatar(who.isEmpty ? '?' : who, size: 52),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  if (state.displayName?.isNotEmpty ?? false) Text(state.displayName!, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                  if (state.signedInEmail?.isNotEmpty ?? false) Text(l.signedInAs(state.signedInEmail!), style: theme.textTheme.bodySmall),
                ]),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(children: [
              DropdownButtonFormField<String?>(
                initialValue: state.locale?.languageCode,
                decoration: InputDecoration(labelText: l.language, prefixIcon: const Icon(Icons.translate)),
                items: const [
                  DropdownMenuItem(value: null, child: Text('System')),
                  DropdownMenuItem(value: 'en', child: Text('English')),
                  DropdownMenuItem(value: 'fr', child: Text('Français')),
                  DropdownMenuItem(value: 'ar', child: Text('العربية')),
                ],
                onChanged: (v) => state.setLocale(v),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _server,
                keyboardType: TextInputType.url,
                textDirection: TextDirection.ltr,
                decoration: InputDecoration(labelText: l.server, prefixIcon: const Icon(Icons.dns_outlined)),
                onSubmitted: state.setServer,
              ),
            ]),
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(50), foregroundColor: theme.colorScheme.error, side: BorderSide(color: theme.colorScheme.error.withValues(alpha: 0.5))),
          icon: const Icon(Icons.logout),
          label: Text(l.signOut),
          onPressed: () async {
            await state.signOut();
            if (context.mounted) Navigator.of(context).popUntil((r) => r.isFirst);
          },
        ),
        const SizedBox(height: 24),
        Text(l.offlineOcrNote, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline)),
      ]),
    );
  }
}
