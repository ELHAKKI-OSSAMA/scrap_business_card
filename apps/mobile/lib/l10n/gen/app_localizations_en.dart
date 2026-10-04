// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Business Card Scanner';

  @override
  String get cardScanner => 'Business Card Scanner';

  @override
  String get newScan => 'New scan';

  @override
  String get front => 'Front';

  @override
  String get back => 'Back';

  @override
  String get optional => 'optional';

  @override
  String get scanDocument => 'Scan (auto-crop)';

  @override
  String get camera => 'Camera';

  @override
  String get gallery => 'Gallery';

  @override
  String get crop => 'Crop & rotate';

  @override
  String get retake => 'Retake';

  @override
  String get remove => 'Remove';

  @override
  String get saveDraft => 'Save draft';

  @override
  String get submit => 'Save & process';

  @override
  String get title => 'Title (optional)';

  @override
  String get search => 'Search drafts…';

  @override
  String get noDrafts => 'No scans yet. Tap + to capture a document.';

  @override
  String get statusLocalDraft => 'Local draft';

  @override
  String get statusPendingUpload => 'Pending upload';

  @override
  String get statusProcessing => 'Processing';

  @override
  String get statusCompleted => 'Completed';

  @override
  String get statusFailed => 'Failed';

  @override
  String get offlineBanner =>
      'Offline — drafts are saved on this device and uploaded when the connection returns. OCR runs on the server.';

  @override
  String get syncNow => 'Sync now';

  @override
  String get syncing => 'Syncing…';

  @override
  String get settings => 'Settings';

  @override
  String get language => 'Language';

  @override
  String get server => 'Server URL';

  @override
  String get signIn => 'Sign in';

  @override
  String get signOut => 'Sign out';

  @override
  String get email => 'E-mail';

  @override
  String get password => 'Password';

  @override
  String get register => 'Create account';

  @override
  String signedInAs(String email) {
    return 'Signed in as $email';
  }

  @override
  String get notSignedIn =>
      'Not signed in. Drafts stay on this device until you sign in.';

  @override
  String get needImage => 'Add at least the front image.';

  @override
  String get delete => 'Delete';

  @override
  String get deleteConfirm =>
      'Delete this draft and its images from the device?';

  @override
  String get cancel => 'Cancel';

  @override
  String get extracted => 'Extracted fields';

  @override
  String get ocrText => 'Recognised text';

  @override
  String get notFound => 'Not found';

  @override
  String get needsReview => 'Needs review';

  @override
  String confidence(int value) {
    return 'Confidence $value%';
  }

  @override
  String get edit => 'Edit';

  @override
  String get save => 'Save';

  @override
  String get retry => 'Retry';

  @override
  String uploadProgress(int percent) {
    return 'Uploading $percent%';
  }

  @override
  String get errorGeneric => 'Something went wrong.';

  @override
  String get errorNetwork => 'Cannot reach the server.';

  @override
  String get errorAuth => 'Incorrect e-mail or password.';

  @override
  String get fullName => 'Full name';

  @override
  String get arabicName => 'Arabic name';

  @override
  String get jobTitle => 'Job title';

  @override
  String get company => 'Company';

  @override
  String get phones => 'Phones';

  @override
  String get emails => 'E-mail';

  @override
  String get website => 'Website';

  @override
  String get address => 'Address';

  @override
  String get offlineOcrNote =>
      'This app does not run OCR on the device: recognition happens after upload.';

  @override
  String lastError(String message) {
    return 'Last error: $message';
  }

  @override
  String get specialty => 'Specialty';

  @override
  String get professionalDescription => 'Professional description';

  @override
  String qrDiffers(String fields) {
    return 'The QR code differs from the printed card for: $fields. Nothing was changed automatically.';
  }

  @override
  String get inferredNote =>
      'Inferred, not printed on the card — please confirm';

  @override
  String get welcome => 'Welcome';

  @override
  String get loginSubtitle => 'Sign in to scan and manage your business cards.';

  @override
  String get advanced => 'Advanced';

  @override
  String get registrationClosed =>
      'Sign-up is closed. Ask the administrator for an account.';

  @override
  String get totalCards => 'Cards';

  @override
  String get toReview => 'To review';

  @override
  String get pendingSection => 'Waiting to be sent';

  @override
  String get myCards => 'My cards';

  @override
  String get emptyTitle => 'No cards yet';

  @override
  String get emptyBody =>
      'Scan your first business card: the text is read and the contact is filled in for you.';

  @override
  String get scanCard => 'Scan a card';

  @override
  String get copied => 'Copied';

  @override
  String get deleteCard => 'Delete this card';

  @override
  String get deleted => 'Card deleted';

  @override
  String get refresh => 'Refresh';

  @override
  String get favorite => 'Favourite';

  @override
  String hello(String name) {
    return 'Hello $name';
  }

  @override
  String get tapToCopy => 'Tap a value to copy it';

  @override
  String get noResults => 'No results';

  @override
  String get burstTitle => 'Camera for the PC';

  @override
  String get burstHint =>
      'Shoot cards one after another: each card is sent immediately and appears live on your PC (website → “Phone camera”, same account).';

  @override
  String get burstShoot => 'Photograph a card';

  @override
  String get burstFrontReady => 'Front captured';

  @override
  String get burstSendNow => 'Send (front only)';

  @override
  String get burstAddBack => 'Add the back, then send';

  @override
  String get burstRetake => 'Retake';

  @override
  String burstCardN(int n) {
    return 'Card $n';
  }

  @override
  String get burstDone => 'Analysed — visible on the PC';

  @override
  String get burstFailed => 'Failed';

  @override
  String get burstProcessing => 'Analysing…';

  @override
  String get burstSending => 'Sending…';
}
