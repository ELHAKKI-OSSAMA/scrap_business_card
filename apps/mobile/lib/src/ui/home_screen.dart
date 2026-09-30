import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../app_state.dart';
import '../drafts/draft.dart';
import '../drafts/draft_store.dart';
import '../modules/product.dart';
import '../sync/sync_service.dart';
import 'capture_screen.dart';
import 'review_screen.dart';
import 'settings_screen.dart';
import 'widgets.dart';

/// Business-card drafts, search, sync and the "new scan" entry point.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = context.watch<AppState>();
    final sync = context.watch<SyncService>();
    final module = ProductModule.businessCard;
    return Scaffold(
      appBar: AppBar(
        title: Text(module.title(l)),
        actions: [
          IconButton(
            tooltip: sync.running ? l.syncing : l.syncNow,
            icon: sync.running ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.sync),
            onPressed: sync.running ? null : () => sync.syncAll(),
          ),
          IconButton(tooltip: l.settings, icon: const Icon(Icons.settings_outlined), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()))),
        ],
      ),
      body: Column(children: [
        if (!state.online) const OfflineBanner(),
        if (state.signedInEmail == null)
          ListTile(leading: const Icon(Icons.info_outline), title: Text(l.notSignedIn), dense: true,
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()))),
        Expanded(child: DraftList(module: module)),
      ]),
      floatingActionButton: FloatingActionButton.large(
        tooltip: l.newScan,
        backgroundColor: module.color,
        foregroundColor: Colors.white,
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => CaptureScreen(module: module))),
        child: const Icon(Icons.add_a_photo_outlined, size: 36),
      ),
    );
  }
}

class DraftList extends StatefulWidget {
  const DraftList({super.key, required this.module});
  final ProductModule module;
  @override
  State<DraftList> createState() => _DraftListState();
}

class _DraftListState extends State<DraftList> {
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final sync = context.watch<SyncService>();
    final drafts = context.watch<DraftStore>().all.where((d) => d.product == widget.module.key && (_q.isEmpty || d.searchText.contains(_q.toLowerCase()))).toList();
    return Column(children: [
      Padding(
        padding: const EdgeInsetsDirectional.fromSTEB(12, 8, 12, 4),
        child: TextField(
          decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: l.search, border: const OutlineInputBorder(), isDense: true),
          onChanged: (v) => setState(() => _q = v),
        ),
      ),
      Expanded(
        child: drafts.isEmpty
            ? Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(l.noDrafts, textAlign: TextAlign.center)))
            : ListView.separated(
                itemCount: drafts.length,
                separatorBuilder: (_, _) => const Divider(height: 1),
                itemBuilder: (context, i) {
                  final d = drafts[i];
                  final thumb = d.images['front'] ?? d.images['back'];
                  final pct = sync.progress[d.localId];
                  return ListTile(
                    leading: thumb != null && File(thumb).existsSync()
                        ? ClipRRect(borderRadius: BorderRadius.circular(6), child: Image.file(File(thumb), width: 56, height: 56, fit: BoxFit.cover))
                        : Icon(widget.module.icon, size: 40),
                    title: Text(_title(d, l), maxLines: 1, overflow: TextOverflow.ellipsis),
                    subtitle: Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                      StatusChip(d.status),
                      if (pct != null) Text(l.uploadProgress(pct)),
                      if (d.error != null) Text(l.lastError(d.error!), style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12)),
                    ]),
                    onTap: () => Navigator.push(context, MaterialPageRoute(
                        builder: (_) => d.status == DraftStatus.completed ? ReviewScreen(draft: d) : CaptureScreen(module: widget.module, draft: d))),
                  );
                },
              ),
      ),
    ]);
  }

  String _title(Draft d, AppLocalizations l) {
    String? v(String k) => (d.result?[k] as Map?)?['value']?.toString();
    return d.title?.isNotEmpty == true ? d.title! : (v('full_name') ?? v('arabic_name') ?? '${widget.module.title(l)} · ${d.createdAt.toLocal().toString().substring(0, 16)}');
  }
}
