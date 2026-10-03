import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';
import '../drafts/draft.dart';
import '../modules/product.dart';
import 'theme.dart';

/// Shows server-extracted fields of one card (by server id, or from a local draft's result);
/// tap a value to copy it; edits and deletion are sent to the API.
class ReviewScreen extends StatefulWidget {
  const ReviewScreen({super.key, this.serverId, this.draft}) : assert(serverId != null || draft != null);
  final String? serverId;
  final Draft? draft;
  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  RemoteDoc? _doc;
  String? _error;

  ProductModule get module => ProductModule.businessCard;
  String? get _id => widget.serverId ?? widget.draft?.serverId;
  Map<String, dynamic>? get data => _doc?.data ?? widget.draft?.result;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    final state = context.read<AppState>();
    if (_id == null) return;
    try {
      final doc = await state.api.getDocument(module.route, _id!);
      if (widget.draft != null) {
        widget.draft!.result = doc.data;
        await state.store.save(widget.draft!);
      }
      if (mounted) setState(() { _doc = doc; _error = null; });
    } on NetworkException {
      if (mounted) setState(() => _error = AppLocalizations.of(context).errorNetwork);
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.status == 404) {
        // deleted elsewhere (web): drop it here too
        await state.loadDocs();
        if (mounted) Navigator.pop(context);
        return;
      }
      setState(() => _error = e.message);
    }
  }

  Future<void> _copy(String value) async {
    await Clipboard.setData(ClipboardData(text: value));
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text('${AppLocalizations.of(context).copied} : $value', maxLines: 2), behavior: SnackBarBehavior.floating, duration: const Duration(seconds: 2)));
  }

  Future<void> _delete() async {
    final l = AppLocalizations.of(context);
    final ok = await showDialog<bool>(context: context, builder: (c) => AlertDialog(
      title: Text(l.deleteCard),
      content: Text(l.deleteConfirm),
      actions: [
        TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)),
        FilledButton(style: FilledButton.styleFrom(backgroundColor: Theme.of(c).colorScheme.error, minimumSize: const Size(0, 44)), onPressed: () => Navigator.pop(c, true), child: Text(l.delete)),
      ],
    ));
    if (ok != true || !mounted || _id == null) return;
    try {
      await context.read<AppState>().deleteDocument(_id!);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.deleted), behavior: SnackBarBehavior.floating));
      Navigator.pop(context);
    } on NetworkException {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.errorNetwork)));
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    }
  }

  Future<void> _edit(ReviewField f, String current) async {
    final l = AppLocalizations.of(context);
    final ctrl = TextEditingController(text: current);
    final v = await showDialog<String>(context: context, builder: (c) => AlertDialog(
      title: Text(f.label(l)),
      content: TextField(controller: ctrl, autofocus: true, textDirection: _dirFor(current), maxLines: f.path == 'professional_description' ? 4 : 1),
      actions: [TextButton(onPressed: () => Navigator.pop(c), child: Text(l.cancel)), FilledButton(style: FilledButton.styleFrom(minimumSize: const Size(0, 44)), onPressed: () => Navigator.pop(c, ctrl.text), child: Text(l.save))],
    ));
    if (v == null || !mounted || _id == null) return;
    final state = context.read<AppState>();
    try {
      final doc = await state.api.patchField(module.route, _id!, f.path, v.trim().isEmpty ? null : v.trim(), expectedVersion: _doc?.version);
      if (widget.draft != null) {
        widget.draft!.result = doc.data;
        await state.store.save(widget.draft!);
      }
      setState(() => _doc = doc);
      state.loadDocs();
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

  static String? _v(Map<String, dynamic> d, String k) => (d[k] as Map?)?['value']?.toString();

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final d = data;
    final name = d == null ? '' : (_v(d, 'full_name') ?? _v(d, 'arabic_name') ?? '—');
    final sub = d == null ? '' : [_v(d, 'job_title'), _v(d, 'company')].whereType<String>().join(' · ');
    return Scaffold(
      appBar: AppBar(
        title: Text(l.extracted),
        actions: [
          IconButton(onPressed: _refresh, icon: const Icon(Icons.refresh_rounded), tooltip: l.refresh),
          if (_id != null) IconButton(key: const Key('delete-card'), onPressed: _delete, icon: const Icon(Icons.delete_outline), tooltip: l.deleteCard),
        ],
      ),
      body: d == null
          ? Center(child: _error != null ? Padding(padding: const EdgeInsets.all(24), child: Text(_error!, textAlign: TextAlign.center)) : const CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(padding: const EdgeInsets.fromLTRB(16, 4, 16, 32), children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(children: [
                      InitialsAvatar(name, size: 56),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(name, textDirection: _dirFor(name), style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
                          if (sub.isNotEmpty) Text(sub, style: theme.textTheme.bodySmall),
                        ]),
                      ),
                    ]),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 10, 4, 6),
                  child: Row(children: [
                    Icon(Icons.touch_app_outlined, size: 16, color: theme.colorScheme.outline),
                    const SizedBox(width: 6),
                    Text(l.tapToCopy, style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline)),
                  ]),
                ),
                if (_error != null) Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(_error!, style: TextStyle(color: theme.colorScheme.error))),
                if (_qrDiffering(d).isNotEmpty)
                  Card(
                    key: const Key('qr-differs'),
                    color: Colors.amber.withValues(alpha: 0.15),
                    child: ListTile(leading: const Icon(Icons.qr_code_2), title: Text(l.qrDiffers(_qrDiffering(d).join(', ')))),
                  ),
                for (final f in module.fields) ...[_fieldTile(f, d[f.path] as Map<String, dynamic>?, l), const SizedBox(height: 8)],
                if (d['phones'] is List && (d['phones'] as List).isNotEmpty) ...[
                  _section(l.phones),
                  Card(
                    child: Column(children: [
                      for (final p in (d['phones'] as List).cast<Map<String, dynamic>>())
                        ListTile(
                          leading: Icon(p['type'] == 'mobile' ? Icons.smartphone : p['type'] == 'fax' ? Icons.fax_outlined : Icons.phone_outlined),
                          title: Text('${p['e164'] ?? p['original']}', textDirection: TextDirection.ltr),
                          subtitle: Text('${p['type']} · ${p['original']}', textDirection: TextDirection.ltr),
                          trailing: const Icon(Icons.copy_rounded, size: 18),
                          onTap: () => _copy('${p['e164'] ?? p['original']}'),
                        ),
                    ]),
                  ),
                ],
                if (d['emails'] is List && (d['emails'] as List).isNotEmpty) ...[
                  _section(l.emails),
                  Card(
                    child: Column(children: [
                      for (final e in (d['emails'] as List).cast<Map<String, dynamic>>())
                        ListTile(
                          leading: const Icon(Icons.alternate_email),
                          title: Text('${e['value']}', textDirection: TextDirection.ltr),
                          trailing: const Icon(Icons.copy_rounded, size: 18),
                          onTap: () => _copy('${e['value']}'),
                        ),
                    ]),
                  ),
                ],
                if (d['address'] is Map && ((d['address'] as Map)['original_text'] ?? '').toString().isNotEmpty) ...[
                  _section(l.address),
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.place_outlined),
                      title: Text('${(d['address'] as Map)['original_text']}', textDirection: _dirFor('${(d['address'] as Map)['original_text']}')),
                      trailing: const Icon(Icons.copy_rounded, size: 18),
                      onTap: () => _copy('${(d['address'] as Map)['original_text']}'),
                    ),
                  ),
                ],
              ]),
            ),
    );
  }

  Widget _section(String text) => Padding(
        padding: const EdgeInsets.fromLTRB(4, 14, 4, 8),
        child: Text(text, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
      );

  Widget _fieldTile(ReviewField f, Map<String, dynamic>? fv, AppLocalizations l) {
    final value = fv?['value']?.toString();
    final conf = fv?['confidence'] as num?;
    final needs = fv?['review_status'] == 'needs_review';
    final theme = Theme.of(context);
    return Card(
      color: needs ? Colors.amber.withValues(alpha: 0.10) : null,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: value == null ? null : () => _copy(value),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
          child: Row(children: [
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(f.label(l), style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.outline)),
                const SizedBox(height: 2),
                Text(value ?? l.notFound, textDirection: value == null ? null : _dirFor(value),
                    style: value == null ? theme.textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic, color: theme.colorScheme.outline) : theme.textTheme.bodyLarge),
                if (conf != null || needs || ((fv?['notes'] as String?)?.startsWith('inferred') ?? false))
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Wrap(spacing: 8, children: [
                      if (conf != null) Text(l.confidence((conf * 100).round()), style: theme.textTheme.bodySmall),
                      if (needs) Text(l.needsReview, style: TextStyle(color: Colors.amber.shade900, fontSize: 12, fontWeight: FontWeight.w600)),
                      if ((fv?['notes'] as String?)?.startsWith('inferred') ?? false) Text(l.inferredNote, style: theme.textTheme.bodySmall),
                    ]),
                  ),
              ]),
            ),
            IconButton(icon: const Icon(Icons.edit_outlined), tooltip: l.edit, onPressed: _id == null ? null : () => _edit(f, value ?? '')),
          ]),
        ),
      ),
    );
  }
}
