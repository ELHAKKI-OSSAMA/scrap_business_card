import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../l10n/gen/app_localizations.dart';
import '../api/api_client.dart';
import '../app_state.dart';
import '../drafts/draft.dart';
import '../drafts/draft_store.dart';
import '../modules/product.dart';
import '../sync/sync_service.dart';
import 'capture_screen.dart';
import 'review_screen.dart';
import 'settings_screen.dart';
import 'theme.dart';
import 'widgets.dart';

/// Server cards (source of truth, also those created on the web), scans waiting to be sent,
/// search, pull-to-refresh and the "scan a card" entry point.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _q = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final s = context.read<AppState>();
      if (s.docs == null && !s.loadingDocs) s.refreshAll();
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final state = context.watch<AppState>();
    final sync = context.watch<SyncService>();
    final store = context.watch<DraftStore>();
    final module = ProductModule.businessCard;
    final q = _q.trim().toLowerCase();

    final pending = store.all.where((d) => d.product == module.key && d.status != DraftStatus.completed && (q.isEmpty || d.searchText.contains(q))).toList();
    final docs = (state.docs ?? const <DocSummary>[]).where((d) => q.isEmpty || d.searchText.contains(q)).toList();
    final total = state.docs?.length ?? 0;
    final toReview = state.docs?.where((d) => d.reviewStatus == 'needs_review').length ?? 0;
    final busy = sync.running || state.loadingDocs;

    return Scaffold(
      body: RefreshIndicator(
        onRefresh: state.refreshAll,
        edgeOffset: 120,
        child: CustomScrollView(physics: const AlwaysScrollableScrollPhysics(), slivers: [
          SliverToBoxAdapter(child: _Header(
            greeting: (state.displayName?.isNotEmpty ?? false) ? l.hello(state.displayName!) : l.welcome,
            title: module.title(l),
            total: total,
            toReview: toReview,
            busy: busy,
            onRefresh: busy ? null : state.refreshAll,
            onSettings: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen())),
          )),
          if (!state.online || state.docsError == 'network') const SliverToBoxAdapter(child: Padding(padding: EdgeInsets.fromLTRB(16, 12, 16, 0), child: OfflineBanner())),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
              child: TextField(
                decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: l.search, isDense: true),
                onChanged: (v) => setState(() => _q = v),
              ),
            ),
          ),
          if (pending.isNotEmpty) ...[
            _SectionTitle(l.pendingSection, count: pending.length),
            SliverList.separated(
              itemCount: pending.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (context, i) => Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: _DraftTile(pending[i], module: module, progress: sync.progress[pending[i].localId])),
            ),
          ],
          _SectionTitle(l.myCards, count: state.docs == null ? null : docs.length),
          if (state.docs == null && state.loadingDocs)
            const SliverToBoxAdapter(child: Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator())))
          else if (docs.isEmpty)
            SliverToBoxAdapter(child: _Empty(searching: q.isNotEmpty))
          else
            SliverList.separated(
              itemCount: docs.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (context, i) => Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: _DocTile(docs[i])),
            ),
          const SliverToBoxAdapter(child: SizedBox(height: 110)),
        ]),
      ),
      floatingActionButton: FloatingActionButton.extended(
        tooltip: l.newScan,
        backgroundColor: brandBlue,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.document_scanner_outlined),
        label: Text(l.scanCard, style: const TextStyle(fontWeight: FontWeight.w600)),
        onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => CaptureScreen(module: module))),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.greeting, required this.title, required this.total, required this.toReview, required this.busy, required this.onRefresh, required this.onSettings});
  final String greeting, title;
  final int total, toReview;
  final bool busy;
  final VoidCallback? onRefresh;
  final VoidCallback onSettings;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final t = Theme.of(context).textTheme;
    return Container(
      decoration: const BoxDecoration(gradient: brandGradient, borderRadius: BorderRadius.vertical(bottom: Radius.circular(28))),
      padding: EdgeInsets.fromLTRB(20, MediaQuery.paddingOf(context).top + 12, 12, 22),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(greeting, style: t.bodyMedium?.copyWith(color: Colors.white.withValues(alpha: 0.85))),
              const SizedBox(height: 2),
              Text(title, style: t.titleLarge?.copyWith(color: Colors.white, fontWeight: FontWeight.w700)),
            ]),
          ),
          IconButton(
            tooltip: l.refresh,
            onPressed: onRefresh,
            icon: busy
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.refresh_rounded, color: Colors.white),
          ),
          IconButton(tooltip: l.settings, onPressed: onSettings, icon: const Icon(Icons.settings_outlined, color: Colors.white)),
        ]),
        const SizedBox(height: 18),
        Row(children: [
          Expanded(child: _Stat(icon: Icons.badge_outlined, value: total, label: l.totalCards)),
          const SizedBox(width: 12),
          Expanded(child: _Stat(icon: Icons.fact_check_outlined, value: toReview, label: l.toReview, highlight: toReview > 0)),
          const SizedBox(width: 8),
        ]),
      ]),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.icon, required this.value, required this.label, this.highlight = false});
  final IconData icon;
  final int value;
  final String label;
  final bool highlight;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(16)),
        child: Row(children: [
          Icon(icon, color: highlight ? const Color(0xFFFFD166) : Colors.white),
          const SizedBox(width: 10),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('$value', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700)),
            Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.85), fontSize: 12)),
          ]),
        ]),
      );
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text, {this.count});
  final String text;
  final int? count;
  @override
  Widget build(BuildContext context) => SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 10),
          child: Row(children: [
            Text(text, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700)),
            if (count != null) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(10)),
                child: Text('$count', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Theme.of(context).colorScheme.onPrimaryContainer)),
              ),
            ],
          ]),
        ),
      );
}

class _DocTile extends StatelessWidget {
  const _DocTile(this.d);
  final DocSummary d;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final sub = [d.s('job_title'), d.s('company')].whereType<String>().join(' · ');
    final contact = d.s('email') ?? d.s('phone');
    final needs = d.reviewStatus == 'needs_review';
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ReviewScreen(serverId: d.id))),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            InitialsAvatar(d.displayName),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(child: Text(d.displayName, maxLines: 1, overflow: TextOverflow.ellipsis, style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700))),
                  if (d.favorite) const Icon(Icons.star_rounded, size: 18, color: Color(0xFFF59E0B)),
                ]),
                if (sub.isNotEmpty) Text(sub, maxLines: 1, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodySmall),
                if (contact != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(contact, maxLines: 1, overflow: TextOverflow.ellipsis, textDirection: TextDirection.ltr,
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.primary)),
                  ),
                if (needs || d.status == 'failed' || d.status == 'processing') ...[
                  const SizedBox(height: 6),
                  _Pill(
                    text: d.status == 'failed' ? l.statusFailed : d.status == 'processing' ? l.statusProcessing : l.needsReview,
                    color: d.status == 'failed' ? Colors.red : d.status == 'processing' ? Colors.blue : Colors.amber.shade800,
                  ),
                ],
              ]),
            ),
            Icon(Icons.chevron_right_rounded, color: theme.colorScheme.outline),
          ]),
        ),
      ),
    );
  }
}

class _DraftTile extends StatelessWidget {
  const _DraftTile(this.d, {required this.module, this.progress});
  final Draft d;
  final ProductModule module;
  final int? progress;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final thumb = d.images['front'] ?? d.images['back'];
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => CaptureScreen(module: module, draft: d))),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: thumb != null && File(thumb).existsSync()
                  ? Image.file(File(thumb), width: 56, height: 40, fit: BoxFit.cover)
                  : Container(width: 56, height: 40, color: Theme.of(context).colorScheme.surfaceContainerHighest, child: Icon(module.icon)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(d.title?.isNotEmpty == true ? d.title! : d.createdAt.toLocal().toString().substring(0, 16), maxLines: 1, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 4),
                Wrap(spacing: 8, crossAxisAlignment: WrapCrossAlignment.center, children: [
                  StatusChip(d.status),
                  if (progress != null) Text(l.uploadProgress(progress!), style: Theme.of(context).textTheme.bodySmall),
                ]),
                if (d.error != null) Text(l.lastError(d.error!), style: TextStyle(color: Theme.of(context).colorScheme.error, fontSize: 12)),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.text, required this.color});
  final String text;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(10)),
        child: Text(text, style: TextStyle(color: color, fontSize: 11.5, fontWeight: FontWeight.w600)),
      );
}

class _Empty extends StatelessWidget {
  const _Empty({required this.searching});
  final bool searching;
  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(32, 24, 32, 0),
      child: Column(children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(color: theme.colorScheme.primaryContainer.withValues(alpha: 0.6), shape: BoxShape.circle),
          child: Icon(searching ? Icons.search_off_rounded : Icons.contact_mail_outlined, size: 44, color: theme.colorScheme.primary),
        ),
        const SizedBox(height: 16),
        Text(searching ? l.noResults : l.emptyTitle, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700), textAlign: TextAlign.center),
        if (!searching) ...[
          const SizedBox(height: 6),
          Text(l.emptyBody, textAlign: TextAlign.center, style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
        ],
      ]),
    );
  }
}
