import 'package:flutter/material.dart';

import '../../l10n/gen/app_localizations.dart';

class ReviewField {
  const ReviewField(this.path, this.label);
  final String path;
  final String Function(AppLocalizations) label;
}

/// The business-card module: API route, sides, branding and review fields used by the
/// capture, review and sync screens.
class ProductModule {
  const ProductModule({
    required this.key,
    required this.route,
    required this.sides,
    required this.requiredSides,
    required this.color,
    required this.icon,
    required this.title,
    required this.fields,
    required this.listFields,
  });

  final String key;
  final String route;
  final List<String> sides;
  final Set<String> requiredSides;
  final Color color;
  final IconData icon;
  final String Function(AppLocalizations) title;
  final List<ReviewField> fields;
  final List<String> listFields; // e.g. phones / emails shown as lists

  static final businessCard = ProductModule(
    key: 'business_card',
    route: 'business-cards',
    sides: const ['front', 'back'],
    requiredSides: const {'front'},
    color: const Color(0xFF1F4FD8),
    icon: Icons.badge_outlined,
    title: (l) => l.cardScanner,
    fields: [
      ReviewField('full_name', (l) => l.fullName),
      ReviewField('arabic_name', (l) => l.arabicName),
      ReviewField('job_title', (l) => l.jobTitle),
      ReviewField('company', (l) => l.company),
      ReviewField('specialty', (l) => l.specialty),
      ReviewField('professional_description', (l) => l.professionalDescription),
      ReviewField('website', (l) => l.website),
    ],
    listFields: const ['phones', 'emails'],
  );

  static final all = [businessCard];

  static ProductModule byKey(String key) => all.firstWhere((m) => m.key == key);
}
