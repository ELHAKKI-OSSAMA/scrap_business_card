import 'package:flutter/material.dart';

const brandBlue = Color(0xFF1F4FD8);
const brandIndigo = Color(0xFF3B2FC9);

ThemeData appTheme(Brightness b) {
  final scheme = ColorScheme.fromSeed(seedColor: brandBlue, brightness: b);
  final dark = b == Brightness.dark;
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: dark ? const Color(0xFF0F1320) : const Color(0xFFF4F6FB),
    appBarTheme: AppBarTheme(backgroundColor: Colors.transparent, surfaceTintColor: Colors.transparent, foregroundColor: scheme.onSurface, centerTitle: false),
    cardTheme: CardThemeData(
      elevation: 0,
      color: dark ? const Color(0xFF181D2E) : Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.5))),
      margin: EdgeInsets.zero,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: dark ? const Color(0xFF181D2E) : Colors.white,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outlineVariant)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outlineVariant)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
  );
}

/// Blue to indigo header used on the login and home screens.
const brandGradient = LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [brandBlue, brandIndigo]);

/// Initials avatar with a stable colour per name.
class InitialsAvatar extends StatelessWidget {
  const InitialsAvatar(this.name, {super.key, this.size = 46});
  final String name;
  final double size;

  static const _palette = [Color(0xFF1F4FD8), Color(0xFF0E9F6E), Color(0xFFD97706), Color(0xFFDB2777), Color(0xFF7C3AED), Color(0xFF0891B2), Color(0xFFDC2626)];

  @override
  Widget build(BuildContext context) {
    final parts = name.trim().split(RegExp(r'\s+')).where((p) => p.isNotEmpty && p != '—').toList();
    final initials = parts.isEmpty
        ? '?'
        : (parts.length == 1 ? parts[0].characters.first : parts[0].characters.first + parts[1].characters.first).toUpperCase();
    final color = _palette[name.codeUnits.fold<int>(0, (a, c) => a + c) % _palette.length];
    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(size / 3)),
      child: Text(initials, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: size * 0.36)),
    );
  }
}
