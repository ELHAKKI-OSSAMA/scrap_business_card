import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ocr_suite_mobile/l10n/gen/app_localizations.dart';
import 'package:ocr_suite_mobile/src/api/api_client.dart';
import 'package:ocr_suite_mobile/src/app_state.dart';
import 'package:ocr_suite_mobile/src/drafts/draft.dart';
import 'package:ocr_suite_mobile/src/drafts/draft_store.dart';
import 'package:ocr_suite_mobile/src/modules/product.dart';
import 'package:ocr_suite_mobile/src/sync/sync_service.dart';
import 'package:ocr_suite_mobile/src/ui/review_screen.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fakes.dart';

/// Business Card module only. Result data below is a hand-written API response shape
/// (no OCR runs in widget tests).
Map<String, dynamic> fv(String? v, {double? c, String status = 'unreviewed', String? notes}) =>
    {'value': v, 'original_value': v, 'confidence': c, 'review_status': status, 'notes': notes, 'source_region_ids': ['f-0']};

final medicalResult = <String, dynamic>{
  'full_name': fv('ELALAMI IDRISSI Rachid', c: 0.9),
  'arabic_name': fv(null),
  'job_title': fv('Médecin', c: 0.5, status: 'needs_review', notes: "inferred: honorific 'Dr' + printed medical specialty; not printed as a title"),
  'company': fv("CABINET D'HÉPATO-GASTROENTÉROLOGIE", c: 0.8),
  'specialty': fv('HÉPATO-GASTROENTÉROLOGIE', c: 0.8, notes: 'explicit specialty term printed on the card'),
  'professional_description': fv("Spécialiste des maladies du foie et de l'appareil digestif", c: 0.8),
  'website': fv(null),
  'phones': [
    {'original': '05.35.51.11.67', 'type': 'phone', 'e164': null},
  ],
  'emails': [],
  'qr_checks': [
    {'field': 'phones', 'qr_id': 'f-qr0', 'qr_value': '+212661000111', 'ocr_value': null, 'status': 'qr_only'},
    {'field': 'full_name', 'qr_id': 'f-qr0', 'qr_value': 'Rachid Elalami', 'ocr_value': 'ELALAMI IDRISSI Rachid', 'status': 'match'},
  ],
};

void main() {
  late Directory tmp;
  late StreamController<bool> conn;

  setUp(() async {
    tmp = await Directory.systemTemp.createTemp('ocr_bc_test');
    conn = StreamController<bool>.broadcast();
  });
  tearDown(() async {
    await conn.close();
    await tmp.delete(recursive: true);
  });

  Future<AppState> state() async {
    SharedPreferences.setMockInitialValues({});
    final store = DraftStore(Directory('${tmp.path}/d'));
    await store.load();
    return AppState(
      prefs: await SharedPreferences.getInstance(),
      api: HttpOcrApi(baseUrl: 'http://unused.invalid', tokens: MemoryTokenStore()),
      store: store,
      sync: SyncService(store: store, api: FakeServer()..offline = true),
      connectivity: conn.stream,
    );
  }

  Future<void> pumpReview(WidgetTester t, AppState s, String locale, Map<String, dynamic> result) async {
    final d = Draft(localId: 'bc', product: 'business_card', status: DraftStatus.completed, result: result);
    await t.pumpWidget(ChangeNotifierProvider<AppState>.value(
      value: s,
      child: MaterialApp(
        locale: Locale(locale),
        supportedLocales: AppLocalizations.supportedLocales,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        home: ReviewScreen(draft: d),
      ),
    ));
    await t.pumpAndSettle();
  }

  test('business card module declares its own fields and sides', () {
    final m = ProductModule.businessCard;
    expect(m.route, 'business-cards');
    expect(m.sides, ['front', 'back']);
    expect(m.requiredSides, {'front'});
    expect(m.fields.map((f) => f.path), containsAll(['full_name', 'arabic_name', 'job_title', 'company', 'specialty', 'professional_description', 'website']));
  });

  testWidgets('medical card review in French: specialty, description, inferred title flagged, phone kept as printed', (t) async {
    final s = await t.runAsync(state);
    await pumpReview(t, s!, 'fr', medicalResult);
    final l = lookupAppLocalizations(const Locale('fr'));
    expect(Directionality.of(t.element(find.byType(Scaffold))), TextDirection.ltr);
    expect(find.text('HÉPATO-GASTROENTÉROLOGIE'), findsOneWidget);
    expect(find.text(l.inferredNote), findsOneWidget);
    expect(find.text(l.needsReview), findsWidgets);
    await t.scrollUntilVisible(find.text('05.35.51.11.67'), 200);
    expect(find.text('05.35.51.11.67'), findsOneWidget);
  });

  testWidgets('QR differences are shown, never applied', (t) async {
    final s = await t.runAsync(state);
    await pumpReview(t, s!, 'en', medicalResult);
    expect(find.byKey(const Key('qr-differs')), findsOneWidget);
    expect(find.textContaining('phones'), findsWidgets);
    expect(find.text('+212661000111'), findsNothing, reason: 'QR-only phone is not added to the contact');
  });

  testWidgets('Arabic UI is RTL and Arabic values are RTL', (t) async {
    final s = await t.runAsync(state);
    await pumpReview(t, s!, 'ar', {
      'full_name': fv('كريم بناني', c: 0.9),
      'arabic_name': fv('كريم بناني', c: 0.9),
      'job_title': fv('مدير المبيعات', c: 0.9),
      'phones': [],
      'emails': [],
    });
    expect(Directionality.of(t.element(find.byType(Scaffold))), TextDirection.rtl);
    expect(find.text(lookupAppLocalizations(const Locale('ar')).extracted), findsOneWidget);
    for (final w in t.widgetList<Text>(find.text('كريم بناني'))) {
      expect(w.textDirection, TextDirection.rtl);
    }
  });

  testWidgets('English UI is LTR', (t) async {
    final s = await t.runAsync(state);
    await pumpReview(t, s!, 'en', {'full_name': fv('James Carter', c: 0.95), 'phones': [], 'emails': []});
    expect(Directionality.of(t.element(find.byType(Scaffold))), TextDirection.ltr);
    expect(find.text('James Carter'), findsOneWidget);
  });
}
