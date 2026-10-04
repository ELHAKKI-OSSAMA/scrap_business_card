import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';
import '../sync/shrink.dart';
import 'theme.dart';

class _Sent {
  _Sent(this.n);
  final int n;
  String status = 'sending'; // sending | processing | completed | failed
  String? error;
}

/// "Phone as camera": shoot card after card; each one is uploaded and processed in the
/// background and appears live on the PC (web → "Phone camera" page, same account).
class BurstScreen extends StatefulWidget {
  const BurstScreen({super.key});
  @override
  State<BurstScreen> createState() => _BurstScreenState();
}

class _BurstScreenState extends State<BurstScreen> {
  static const _route = 'business-cards';
  File? _front;
  final List<_Sent> _sent = [];
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

  Future<void> _send(File front, File? back) async {
    final api = context.read<AppState>().api;
    final state = context.read<AppState>();
    final s = _Sent(_sent.length + 1);
    setState(() {
      _front = null;
      _sent.insert(0, s);
    });
    try {
      final doc = await api.createDocument(_route, clientRef: const Uuid().v4());
      await api.uploadImage(_route, doc.id, 'front', await shrinkForUpload(front));
      if (back != null) await api.uploadImage(_route, doc.id, 'back', await shrinkForUpload(back));
      if (mounted) setState(() => s.status = 'processing');
      final job = await api.process(_route, doc.id);
      s.status = job.status == 'failed' ? 'failed' : 'completed';
      s.error = job.errorMessage;
      state.loadDocs();
    } catch (e) {
      s.status = 'failed';
      s.error = '$e';
    }
    if (mounted) setState(() {});
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
        Text(l.burstHint, style: theme.textTheme.bodyMedium),
        const SizedBox(height: 16),
        if (_front == null)
          InkWell(
            key: const Key('burst-shoot'),
            borderRadius: BorderRadius.circular(24),
            onTap: () async {
              final f = await _shoot();
              if (f != null) setState(() => _front = f);
            },
            child: Ink(
              height: 180,
              decoration: BoxDecoration(gradient: brandGradient, borderRadius: BorderRadius.circular(24)),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                const Icon(Icons.photo_camera_rounded, size: 48, color: Colors.white),
                const SizedBox(height: 8),
                Text(l.burstShoot, style: theme.textTheme.titleMedium?.copyWith(color: Colors.white, fontWeight: FontWeight.w700)),
              ]),
            ),
          )
        else
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                Row(children: [
                  ClipRRect(borderRadius: BorderRadius.circular(8), child: Image.file(_front!, width: 72, height: 46, fit: BoxFit.cover)),
                  const SizedBox(width: 12),
                  Expanded(child: Text(l.burstFrontReady, style: theme.textTheme.titleSmall)),
                ]),
                const SizedBox(height: 12),
                FilledButton.icon(onPressed: () => _send(_front!, null), icon: const Icon(Icons.send_rounded), label: Text(l.burstSendNow)),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () async {
                    final b = await _shoot();
                    if (b != null && _front != null) await _send(_front!, b);
                  },
                  icon: const Icon(Icons.flip_rounded),
                  label: Text(l.burstAddBack),
                ),
                TextButton.icon(onPressed: () => setState(() => _front = null), icon: const Icon(Icons.replay_rounded), label: Text(l.burstRetake)),
              ]),
            ),
          ),
        const SizedBox(height: 16),
        for (final s in _sent)
          Card(
            child: ListTile(
              leading: switch (s.status) {
                'completed' => const Icon(Icons.check_circle_rounded, color: Colors.green),
                'failed' => Icon(Icons.error_rounded, color: theme.colorScheme.error),
                _ => const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2.5)),
              },
              title: Text(l.burstCardN(s.n)),
              subtitle: Text(switch (s.status) {
                'completed' => l.burstDone,
                'failed' => s.error ?? l.burstFailed,
                'processing' => l.burstProcessing,
                _ => l.burstSending,
              }, maxLines: 2, overflow: TextOverflow.ellipsis),
            ),
          ),
      ]),
    );
  }
}
