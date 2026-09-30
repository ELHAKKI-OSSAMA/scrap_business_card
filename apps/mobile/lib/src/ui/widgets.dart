import 'package:flutter/material.dart';

import '../../l10n/gen/app_localizations.dart';
import '../drafts/draft.dart';

String statusLabel(AppLocalizations l, DraftStatus s) => switch (s) {
      DraftStatus.localDraft => l.statusLocalDraft,
      DraftStatus.pendingUpload => l.statusPendingUpload,
      DraftStatus.processing => l.statusProcessing,
      DraftStatus.completed => l.statusCompleted,
      DraftStatus.failed => l.statusFailed,
    };

class StatusChip extends StatelessWidget {
  const StatusChip(this.status, {super.key});
  final DraftStatus status;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    final (bg, fg, icon) = switch (status) {
      DraftStatus.localDraft => (scheme.surfaceContainerHighest, scheme.onSurfaceVariant, Icons.edit_note),
      DraftStatus.pendingUpload => (Colors.amber.shade100, Colors.amber.shade900, Icons.cloud_upload_outlined),
      DraftStatus.processing => (Colors.blue.shade100, Colors.blue.shade900, Icons.hourglass_top),
      DraftStatus.completed => (Colors.green.shade100, Colors.green.shade900, Icons.check_circle_outline),
      DraftStatus.failed => (Colors.red.shade100, Colors.red.shade900, Icons.error_outline),
    };
    return Semantics(
      label: statusLabel(l, status),
      child: Container(
        padding: const EdgeInsetsDirectional.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(12)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon, size: 14, color: fg),
          const SizedBox(width: 4),
          Text(statusLabel(l, status), style: TextStyle(color: fg, fontSize: 12, fontWeight: FontWeight.w600)),
        ]),
      ),
    );
  }
}

class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key});
  @override
  Widget build(BuildContext context) => MaterialBanner(
        leading: const Icon(Icons.cloud_off),
        content: Text(AppLocalizations.of(context).offlineBanner),
        actions: const [SizedBox.shrink()],
      );
}
