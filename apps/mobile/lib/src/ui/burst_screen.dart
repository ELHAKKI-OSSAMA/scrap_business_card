import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';
import '../sync/shrink.dart';

/// Phone side of "phone as camera": answers the PC's photo requests (web → New card → "Phone camera").
class BurstScreen extends StatefulWidget {
  const BurstScreen({super.key});
  @override
  State<BurstScreen> createState() => _BurstScreenState();
}

class _BurstScreenState extends State<BurstScreen> {
  CaptureRequest? _req;
  bool _reqBusy = false;
  String? _reqError;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    // The PC may ask for a specific photo (web → New card → "Phone camera").
    _tick();
    _poll = Timer.periodic(const Duration(milliseconds: 2500), (_) => _tick());
  }

  @override
  void dispose() {
    _poll?.cancel();
    super.dispose();
  }

  Future<void> _tick() async {
    if (_reqBusy) return;
    try {
      final r = await context.read<AppState>().api.pendingCapture();
      if (mounted && r?.id != _req?.id) setState(() => _req = r);
    } catch (_) {/* offline: retry on next tick */}
  }

  Future<void> _answer() async {
    final req = _req;
    if (req == null) return;
    final api = context.read<AppState>().api;
    final f = await _shoot();
    if (f == null) return;
    setState(() {
      _reqBusy = true;
      _reqError = null;
    });
    try {
      await api.uploadImage(req.route, req.documentId, req.side, await shrinkForUpload(f));
      await api.finishCapture(req.id);
      _req = null;
    } catch (e) {
      _reqError = '$e';
    }
    if (mounted) setState(() => _reqBusy = false);
  }

  Future<File?> _shoot() async {
    final x = await ImagePicker().pickImage(source: ImageSource.camera, imageQuality: 92, maxWidth: 4000);
    return x == null ? null : File(x.path);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.burstTitle)),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (_req != null) ...[
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: theme.colorScheme.primary, width: 2)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                Text(l.burstPcAsks(_req!.side == 'back' ? l.burstBack : l.burstFront), style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 12),
                FilledButton.icon(
                  key: const Key('answer-pc'),
                  onPressed: _reqBusy ? null : _answer,
                  icon: _reqBusy ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.photo_camera_rounded),
                  label: Text(l.burstShootForPc),
                ),
                if (_reqError != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_reqError!, style: TextStyle(color: theme.colorScheme.error))),
                TextButton(
                  onPressed: _reqBusy ? null : () {
                    context.read<AppState>().api.finishCapture(_req!.id, done: false).catchError((_) {});
                    setState(() => _req = null);
                  },
                  child: Text(l.cancel),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 16),
        ],
        if (_req == null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(children: [
                Icon(Icons.screen_share_outlined, size: 44, color: theme.colorScheme.primary),
                const SizedBox(height: 12),
                Text(l.burstWaitingPc, style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
                const SizedBox(height: 6),
                Text(l.burstWaitingPcHint, style: theme.textTheme.bodySmall, textAlign: TextAlign.center),
              ]),
            ),
          ),
      ]),
    );
  }
}
