import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';
import '../drafts/draft.dart';
import '../modules/product.dart';

/// Shows server-extracted fields; edits are sent to the API (review requires connectivity).
class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key, required this.draft});
  final Draft draft;
  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  RemoteDoc? _doc;
  String? _error;

  ProductModule get module => ProductModule.byKey(widget.draft.product);
  Map<String, dynamic>? get data => _doc?.data ?? widget.draft.result;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    final state = context.read<AppState>();
    if (widget.draft.serverId == null) return;
    try {
      final doc = await state.api.getDocument(module.route, widget.draft.serverId!);
      widget.draft.result = doc.data;
      await state.store.save(widget.draft);
      if (mounted) setState(() => _doc = doc);
    } on NetworkException {
      if (mounted) setState(() => _error = AppLocalizations.of(context).errorNetwork);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    }
  }

  Future<void> _edit(ReviewField f, String current) async {
    final l = AppLocalizations.of(context);
    final ctrl = TextEditingController(text: current);
    final v = await showDialog<String>(context: context, builder: (c) => AlertDialog(
      title: Text(f.label(l)),
      content: TextField(controller: ctrl, autofocus: true, textDirection: _dirFor(current), maxLines: f.path == 'message' ? 6 : 1),
      actions: [TextButton(onPressed: () => Navigator.pop(c), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, ctrl.text), child: Text(l.save))],
    ));
    if (v == null || !mounted) return;
    final state = context.read<AppState>();
    try {
      final doc = await state.api.patchField(module.route, widget.draft.serverId!, f.path, v.trim().isEmpty ? null : v.trim(), expectedVersion: _doc?.version);
      widget.draft.result = doc.data;
      await state.store.save(widget.draft);
      setState(() => _doc = doc);
    } on NetworkException {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.errorNetwork)));
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  /// Fields where the QR code and the printed text disagree (business cards); never auto-resolved.
  static List<String> _qrDiffering(Map<String, dynamic> d) => <String>{
        for (final c in (d['qr_checks'] as List? ?? const []).cast<Map<String, dynamic>>())
          if (c['status'] != 'match') c['field'] as String,
      }.toList();

  static TextDirection? _dirFor(String s) => RegExp(r'[؀-ۿ]').hasMatch(s) ? TextDirection.rtl : null;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final d = data;
    return Scaffold(
      appBar: AppBar(title: Text(l.extracted), actions: [IconButton(onPressed: _refresh, icon: const Icon(Icons.refresh), tooltip: l.retry)]),
      body: d == null
          ? Center(child: _error != null ? Text(_error!) : const CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(padding: const EdgeInsets.all(12), children: [
                if (_error != null) Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
                if (_qrDiffering(d).isNotEmpty)
                  Card(
                    key: const Key('qr-differs'),
                    color: Colors.amber.withValues(alpha: 0.15),
                    child: ListTile(leading: const Icon(Icons.qr_code_2), title: Text(l.qrDiffers(_qrDiffering(d).join(', ')))),
                  ),
                for (final f in module.fields) _fieldTile(f, d[f.path] as Map<String, dynamic>?, l),
                if (d['phones'] is List && (d['phones'] as List).isNotEmpty) ...[
                  Padding(padding: const EdgeInsets.fromLTRB(8, 12, 8, 4), child: Text(l.phones, style: Theme.of(context).textTheme.titleSmall)),
                  for (final p in (d['phones'] as List).cast<Map<String, dynamic>>())
                    ListTile(dense: true, leading: const Icon(Icons.phone_outlined), title: Text(p['original'] as String, textDirection: TextDirection.ltr),
                        subtitle: Text('${p['type']} · ${p['e164'] ?? '—'}', textDirection: TextDirection.ltr)),
                ],
                if (d['emails'] is List && (d['emails'] as List).isNotEmpty) ...[
                  Padding(padding: const EdgeInsets.fromLTRB(8, 12, 8, 4), child: Text(l.emails, style: Theme.of(context).textTheme.titleSmall)),
                  for (final e in (d['emails'] as List).cast<Map<String, dynamic>>())
                    ListTile(dense: true, leading: const Icon(Icons.alternate_email), title: Text('${e['value']}', textDirection: TextDirection.ltr)),
                ],
              ]),
            ),
    );
  }

  Widget _fieldTile(ReviewField f, Map<String, dynamic>? fv, AppLocalizations l) {
    final value = fv?['value']?.toString();
    final conf = fv?['confidence'] as num?;
    final needs = fv?['review_status'] == 'needs_review';
    return Card(
      color: needs ? Colors.amber.withValues(alpha: 0.12) : null,
      child: ListTile(
        title: Text(f.label(l), style: Theme.of(context).textTheme.labelMedium),
        subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(value ?? l.notFound, textDirection: value == null ? null : _dirFor(value),
              style: value == null ? const TextStyle(fontStyle: FontStyle.italic) : Theme.of(context).textTheme.bodyLarge),
          Wrap(spacing: 8, children: [
            if (conf != null) Text(l.confidence((conf * 100).round()), style: Theme.of(context).textTheme.bodySmall),
            if (needs) Text(l.needsReview, style: TextStyle(color: Colors.amber.shade900, fontSize: 12, fontWeight: FontWeight.w600)),
            if ((fv?['notes'] as String?)?.startsWith('inferred') ?? false) Text(l.inferredNote, style: Theme.of(context).textTheme.bodySmall),
          ]),
        ]),
        trailing: IconButton(icon: const Icon(Icons.edit_outlined), tooltip: l.edit, onPressed: widget.draft.serverId == null ? null : () => _edit(f, value ?? '')),
      ),
    );
  }
}
