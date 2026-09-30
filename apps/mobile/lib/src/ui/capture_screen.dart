import 'dart:async';
import 'dart:io';

import 'package:cunning_document_scanner/cunning_document_scanner.dart';
import 'package:flutter/material.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';

import '../../l10n/gen/app_localizations.dart';
import '../app_state.dart';
import '../drafts/draft.dart';
import '../modules/product.dart';
import '../sync/sync_service.dart';

/// Camera-first capture: document scanner (native edge detection + perspective correction),
/// plain camera, or gallery; then optional crop/rotate. Works fully offline (drafts are local).
class CaptureScreen extends StatefulWidget {
  const CaptureScreen({super.key, required this.module, this.draft});
  final ProductModule module;
  final Draft? draft;
  @override
  State<CaptureScreen> createState() => _CaptureScreenState();
}

class _CaptureScreenState extends State<CaptureScreen> {
  late final Draft _draft = widget.draft ?? Draft(localId: const Uuid().v4().replaceAll('-', ''), product: widget.module.key);
  late final TextEditingController _title = TextEditingController(text: _draft.title);
  bool _busy = false;

  Future<void> _set(String side, String? path) async {
    if (path == null) return;
    final store = context.read<AppState>().store;
    await store.importImage(_draft, side, File(path));
    _draft.uploadedSha.remove(side);
    if (_draft.status == DraftStatus.completed || _draft.status == DraftStatus.failed) _draft.status = DraftStatus.localDraft;
    await store.save(_draft);
    setState(() {});
  }

  Future<void> _scan(String side) async {
    try {
      final pics = await CunningDocumentScanner.getPictures(noOfPages: 1, scannerSource: ScannerSource.cameraAndGallery);
      if (pics != null && pics.isNotEmpty) await _set(side, pics.first);
    } catch (_) {
      await _pick(side, ImageSource.camera); // scanner unavailable (e.g. emulator without ML Kit)
    }
  }

  Future<void> _pick(String side, ImageSource src) async {
    final x = await ImagePicker().pickImage(source: src, imageQuality: 92, maxWidth: 4000);
    await _set(side, x?.path);
  }

  Future<void> _crop(String side) async {
    final path = _draft.images[side];
    if (path == null) return;
    final l = AppLocalizations.of(context);
    final c = await ImageCropper().cropImage(sourcePath: path, uiSettings: [
      AndroidUiSettings(toolbarTitle: l.crop, lockAspectRatio: false),
      IOSUiSettings(title: l.crop),
    ]);
    await _set(side, c?.path);
  }

  Future<void> _save({required bool submit}) async {
    final l = AppLocalizations.of(context);
    if (submit && !widget.module.requiredSides.every(_draft.images.containsKey)) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.needImage)));
      return;
    }
    setState(() => _busy = true);
    final state = context.read<AppState>();
    final sync = context.read<SyncService>();
    _draft.title = _title.text.trim().isEmpty ? null : _title.text.trim();
    if (submit) _draft.status = DraftStatus.pendingUpload;
    await state.store.save(_draft);
    if (!mounted) return;
    Navigator.pop(context);
    if (submit && state.online) unawaited(sync.syncAll());
  }

  Future<void> _delete() async {
    final l = AppLocalizations.of(context);
    final ok = await showDialog<bool>(context: context, builder: (c) => AlertDialog(
      content: Text(l.deleteConfirm),
      actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.delete))],
    ));
    if (ok == true && mounted) {
      await context.read<AppState>().store.delete(_draft);
      if (mounted) Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l.newScan),
        actions: [if (widget.draft != null) IconButton(tooltip: l.delete, icon: const Icon(Icons.delete_outline), onPressed: _delete)],
      ),
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.all(16), children: [
          TextField(controller: _title, decoration: InputDecoration(labelText: l.title, border: const OutlineInputBorder())),
          const SizedBox(height: 16),
          for (final side in widget.module.sides) _SideCard(
            side: side,
            label: side == 'front' ? l.front : '${l.back}${widget.module.requiredSides.contains(side) ? '' : ' (${l.optional})'}',
            path: _draft.images[side],
            onScan: () => _scan(side),
            onCamera: () => _pick(side, ImageSource.camera),
            onGallery: () => _pick(side, ImageSource.gallery),
            onCrop: () => _crop(side),
            onRemove: () async {
              final store = context.read<AppState>().store;
              await store.removeImage(_draft, side);
              await store.save(_draft);
              if (mounted) setState(() {});
            },
          ),
          const SizedBox(height: 8),
          Text(l.offlineOcrNote, style: Theme.of(context).textTheme.bodySmall),
        ]),
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(children: [
            Expanded(child: OutlinedButton(onPressed: _busy ? null : () => _save(submit: false), child: Text(l.saveDraft))),
            const SizedBox(width: 12),
            Expanded(child: FilledButton(onPressed: _busy ? null : () => _save(submit: true), child: Text(l.submit))),
          ]),
        ),
      ),
    );
  }
}

class _SideCard extends StatelessWidget {
  const _SideCard({required this.side, required this.label, required this.path, required this.onScan, required this.onCamera, required this.onGallery, required this.onCrop, required this.onRemove});
  final String side;
  final String label;
  final String? path;
  final VoidCallback onScan, onCamera, onGallery, onCrop, onRemove;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(label, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (path != null) ...[
            ClipRRect(borderRadius: BorderRadius.circular(8), child: Image.file(File(path!), height: 200, fit: BoxFit.contain, key: ValueKey(path))),
            Wrap(spacing: 8, children: [
              TextButton.icon(onPressed: onCrop, icon: const Icon(Icons.crop_rotate), label: Text(l.crop)),
              TextButton.icon(onPressed: onScan, icon: const Icon(Icons.replay), label: Text(l.retake)),
              TextButton.icon(onPressed: onRemove, icon: const Icon(Icons.delete_outline), label: Text(l.remove)),
            ]),
          ] else ...[
            FilledButton.icon(onPressed: onScan, icon: const Icon(Icons.document_scanner_outlined, size: 28),
                style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(64)), label: Text(l.scanDocument)),
            const SizedBox(height: 8),
            Row(children: [
              Expanded(child: OutlinedButton.icon(onPressed: onCamera, icon: const Icon(Icons.photo_camera_outlined), label: Text(l.camera))),
              const SizedBox(width: 8),
              Expanded(child: OutlinedButton.icon(onPressed: onGallery, icon: const Icon(Icons.photo_library_outlined), label: Text(l.gallery))),
            ]),
          ],
        ]),
      ),
    );
  }
}
