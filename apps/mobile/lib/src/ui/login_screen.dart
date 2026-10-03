import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';
import 'theme.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(
        body: DecoratedBox(
          decoration: BoxDecoration(gradient: brandGradient),
          child: Center(child: Icon(Icons.badge_rounded, size: 72, color: Colors.white)),
        ),
      );
}

/// Sign-in is required before using the app. Sign-up is offered only if the server allows it.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  late final TextEditingController _server = TextEditingController(text: context.read<AppState>().serverUrl);
  bool _busy = false, _register = false, _showPw = false, _canRegister = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _checkRegistration();
  }

  Future<void> _checkRegistration() async {
    final open = await context.read<AppState>().api.registrationOpen();
    if (mounted) setState(() => _canRegister = open);
  }

  Future<void> _submit() async {
    final l = AppLocalizations.of(context);
    final state = context.read<AppState>();
    if (_email.text.trim().isEmpty || _password.text.isEmpty) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_server.text.trim() != state.serverUrl) await state.setServer(_server.text);
      await state.signIn(_email.text.trim(), _password.text, register: _register);
    } on NetworkException {
      _error = l.errorNetwork;
    } on ApiException catch (e) {
      _error = e.status == 401 ? l.errorAuth : (e.code == 'registration_disabled' ? l.registrationClosed : e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    return Scaffold(
      body: Column(children: [
        Container(
          width: double.infinity,
          decoration: const BoxDecoration(gradient: brandGradient, borderRadius: BorderRadius.vertical(bottom: Radius.circular(32))),
          padding: EdgeInsets.fromLTRB(28, MediaQuery.paddingOf(context).top + 40, 28, 36),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(16)),
              child: const Icon(Icons.badge_rounded, color: Colors.white, size: 34),
            ),
            const SizedBox(height: 20),
            Text(l.appTitle, style: theme.textTheme.headlineSmall?.copyWith(color: Colors.white, fontWeight: FontWeight.w700)),
            const SizedBox(height: 6),
            Text(l.loginSubtitle, style: theme.textTheme.bodyMedium?.copyWith(color: Colors.white.withValues(alpha: 0.85))),
          ]),
        ),
        Expanded(
          child: ListView(padding: const EdgeInsets.fromLTRB(24, 28, 24, 24), children: [
            Text(_register ? l.register : l.welcome, style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 18),
            TextField(
              key: const Key('login-email'),
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              textDirection: TextDirection.ltr,
              autofillHints: const [AutofillHints.email],
              textInputAction: TextInputAction.next,
              decoration: InputDecoration(labelText: l.email, prefixIcon: const Icon(Icons.alternate_email)),
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('login-password'),
              controller: _password,
              obscureText: !_showPw,
              textDirection: TextDirection.ltr,
              autofillHints: const [AutofillHints.password],
              onSubmitted: (_) => _submit(),
              decoration: InputDecoration(
                labelText: l.password,
                prefixIcon: const Icon(Icons.lock_outline),
                suffixIcon: IconButton(
                  icon: Icon(_showPw ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                  onPressed: () => setState(() => _showPw = !_showPw),
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: theme.colorScheme.errorContainer, borderRadius: BorderRadius.circular(12)),
                child: Row(children: [
                  Icon(Icons.error_outline, color: theme.colorScheme.onErrorContainer),
                  const SizedBox(width: 8),
                  Expanded(child: Text(_error!, style: TextStyle(color: theme.colorScheme.onErrorContainer))),
                ]),
              ),
            ],
            const SizedBox(height: 20),
            FilledButton(
              key: const Key('login-submit'),
              onPressed: _busy ? null : _submit,
              child: _busy
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5, color: Colors.white))
                  : Text(_register ? l.register : l.signIn),
            ),
            const SizedBox(height: 12),
            if (_canRegister)
              TextButton(
                onPressed: () => setState(() {
                  _register = !_register;
                  _error = null;
                }),
                child: Text(_register ? l.signIn : l.register),
              )
            else
              Text(l.registrationClosed, textAlign: TextAlign.center, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 16),
            Theme(
              data: theme.copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: EdgeInsets.zero,
                leading: const Icon(Icons.dns_outlined),
                title: Text(l.advanced, style: theme.textTheme.bodyMedium),
                children: [
                  TextField(
                    controller: _server,
                    keyboardType: TextInputType.url,
                    textDirection: TextDirection.ltr,
                    decoration: InputDecoration(labelText: l.server),
                    onSubmitted: (_) => _checkRegistration(),
                  ),
                ],
              ),
            ),
          ]),
        ),
      ]),
    );
  }
}
