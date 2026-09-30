// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String get appTitle => 'ماسح بطاقات الأعمال';

  @override
  String get cardScanner => 'ماسح بطاقات العمل';

  @override
  String get newScan => 'مسح جديد';

  @override
  String get front => 'الوجه';

  @override
  String get back => 'الظهر';

  @override
  String get optional => 'اختياري';

  @override
  String get scanDocument => 'مسح (قص تلقائي)';

  @override
  String get camera => 'الكاميرا';

  @override
  String get gallery => 'المعرض';

  @override
  String get crop => 'قص وتدوير';

  @override
  String get retake => 'إعادة الالتقاط';

  @override
  String get remove => 'إزالة';

  @override
  String get saveDraft => 'حفظ المسودة';

  @override
  String get submit => 'حفظ ومعالجة';

  @override
  String get title => 'العنوان (اختياري)';

  @override
  String get search => 'ابحث في المسودات…';

  @override
  String get noDrafts => 'لا توجد عمليات مسح بعد. اضغط + لالتقاط مستند.';

  @override
  String get statusLocalDraft => 'مسودة محلية';

  @override
  String get statusPendingUpload => 'في انتظار الرفع';

  @override
  String get statusProcessing => 'قيد المعالجة';

  @override
  String get statusCompleted => 'مكتمل';

  @override
  String get statusFailed => 'فشل';

  @override
  String get offlineBanner =>
      'غير متصل — تُحفظ المسودات على هذا الجهاز وتُرفع عند عودة الاتصال. يتم التعرّف الضوئي على الخادم.';

  @override
  String get syncNow => 'مزامنة الآن';

  @override
  String get syncing => 'جارٍ المزامنة…';

  @override
  String get settings => 'الإعدادات';

  @override
  String get language => 'اللغة';

  @override
  String get server => 'عنوان الخادم';

  @override
  String get signIn => 'تسجيل الدخول';

  @override
  String get signOut => 'تسجيل الخروج';

  @override
  String get email => 'البريد الإلكتروني';

  @override
  String get password => 'كلمة المرور';

  @override
  String get register => 'إنشاء حساب';

  @override
  String signedInAs(String email) {
    return 'تم تسجيل الدخول باسم $email';
  }

  @override
  String get notSignedIn =>
      'لم يتم تسجيل الدخول. تبقى المسودات على الجهاز حتى تسجيل الدخول.';

  @override
  String get needImage => 'أضف صورة الوجه على الأقل.';

  @override
  String get delete => 'حذف';

  @override
  String get deleteConfirm => 'حذف هذه المسودة وصورها من الجهاز؟';

  @override
  String get cancel => 'إلغاء';

  @override
  String get extracted => 'الحقول المستخرجة';

  @override
  String get ocrText => 'النص المتعرَّف عليه';

  @override
  String get notFound => 'غير موجود';

  @override
  String get needsReview => 'يحتاج إلى مراجعة';

  @override
  String confidence(int value) {
    return 'الثقة $value٪';
  }

  @override
  String get edit => 'تعديل';

  @override
  String get save => 'حفظ';

  @override
  String get retry => 'إعادة المحاولة';

  @override
  String uploadProgress(int percent) {
    return 'جارٍ الرفع $percent٪';
  }

  @override
  String get errorGeneric => 'حدث خطأ ما.';

  @override
  String get errorNetwork => 'تعذّر الوصول إلى الخادم.';

  @override
  String get errorAuth => 'البريد الإلكتروني أو كلمة المرور غير صحيحة.';

  @override
  String get fullName => 'الاسم الكامل';

  @override
  String get arabicName => 'الاسم بالعربية';

  @override
  String get jobTitle => 'المسمّى الوظيفي';

  @override
  String get company => 'الشركة';

  @override
  String get phones => 'الهواتف';

  @override
  String get emails => 'البريد الإلكتروني';

  @override
  String get website => 'الموقع الإلكتروني';

  @override
  String get address => 'العنوان';

  @override
  String get offlineOcrNote =>
      'لا يُجري هذا التطبيق التعرّف الضوئي على الجهاز: يتم التعرّف بعد الرفع.';

  @override
  String lastError(String message) {
    return 'آخر خطأ: $message';
  }

  @override
  String get specialty => 'التخصص';

  @override
  String get professionalDescription => 'الوصف المهني';

  @override
  String qrDiffers(String fields) {
    return 'رمز QR يختلف عن البطاقة المطبوعة في: $fields. لم يُغيَّر أي شيء تلقائيًا.';
  }

  @override
  String get inferredNote => 'مستنتج وغير مطبوع على البطاقة — يرجى التأكيد';
}
