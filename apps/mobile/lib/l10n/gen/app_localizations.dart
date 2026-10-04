import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';
import 'app_localizations_fr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'gen/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('en'),
    Locale('fr'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'Business Card Scanner'**
  String get appTitle;

  /// No description provided for @cardScanner.
  ///
  /// In en, this message translates to:
  /// **'Business Card Scanner'**
  String get cardScanner;

  /// No description provided for @newScan.
  ///
  /// In en, this message translates to:
  /// **'New scan'**
  String get newScan;

  /// No description provided for @front.
  ///
  /// In en, this message translates to:
  /// **'Front'**
  String get front;

  /// No description provided for @back.
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get back;

  /// No description provided for @optional.
  ///
  /// In en, this message translates to:
  /// **'optional'**
  String get optional;

  /// No description provided for @scanDocument.
  ///
  /// In en, this message translates to:
  /// **'Scan (auto-crop)'**
  String get scanDocument;

  /// No description provided for @camera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get camera;

  /// No description provided for @gallery.
  ///
  /// In en, this message translates to:
  /// **'Gallery'**
  String get gallery;

  /// No description provided for @crop.
  ///
  /// In en, this message translates to:
  /// **'Crop & rotate'**
  String get crop;

  /// No description provided for @retake.
  ///
  /// In en, this message translates to:
  /// **'Retake'**
  String get retake;

  /// No description provided for @remove.
  ///
  /// In en, this message translates to:
  /// **'Remove'**
  String get remove;

  /// No description provided for @saveDraft.
  ///
  /// In en, this message translates to:
  /// **'Save draft'**
  String get saveDraft;

  /// No description provided for @submit.
  ///
  /// In en, this message translates to:
  /// **'Save & process'**
  String get submit;

  /// No description provided for @title.
  ///
  /// In en, this message translates to:
  /// **'Title (optional)'**
  String get title;

  /// No description provided for @search.
  ///
  /// In en, this message translates to:
  /// **'Search drafts…'**
  String get search;

  /// No description provided for @noDrafts.
  ///
  /// In en, this message translates to:
  /// **'No scans yet. Tap + to capture a document.'**
  String get noDrafts;

  /// No description provided for @statusLocalDraft.
  ///
  /// In en, this message translates to:
  /// **'Local draft'**
  String get statusLocalDraft;

  /// No description provided for @statusPendingUpload.
  ///
  /// In en, this message translates to:
  /// **'Pending upload'**
  String get statusPendingUpload;

  /// No description provided for @statusProcessing.
  ///
  /// In en, this message translates to:
  /// **'Processing'**
  String get statusProcessing;

  /// No description provided for @statusCompleted.
  ///
  /// In en, this message translates to:
  /// **'Completed'**
  String get statusCompleted;

  /// No description provided for @statusFailed.
  ///
  /// In en, this message translates to:
  /// **'Failed'**
  String get statusFailed;

  /// No description provided for @offlineBanner.
  ///
  /// In en, this message translates to:
  /// **'Offline — drafts are saved on this device and uploaded when the connection returns. OCR runs on the server.'**
  String get offlineBanner;

  /// No description provided for @syncNow.
  ///
  /// In en, this message translates to:
  /// **'Sync now'**
  String get syncNow;

  /// No description provided for @syncing.
  ///
  /// In en, this message translates to:
  /// **'Syncing…'**
  String get syncing;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @server.
  ///
  /// In en, this message translates to:
  /// **'Server URL'**
  String get server;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'E-mail'**
  String get email;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @register.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get register;

  /// No description provided for @signedInAs.
  ///
  /// In en, this message translates to:
  /// **'Signed in as {email}'**
  String signedInAs(String email);

  /// No description provided for @notSignedIn.
  ///
  /// In en, this message translates to:
  /// **'Not signed in. Drafts stay on this device until you sign in.'**
  String get notSignedIn;

  /// No description provided for @needImage.
  ///
  /// In en, this message translates to:
  /// **'Add at least the front image.'**
  String get needImage;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @deleteConfirm.
  ///
  /// In en, this message translates to:
  /// **'Delete this draft and its images from the device?'**
  String get deleteConfirm;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @extracted.
  ///
  /// In en, this message translates to:
  /// **'Extracted fields'**
  String get extracted;

  /// No description provided for @ocrText.
  ///
  /// In en, this message translates to:
  /// **'Recognised text'**
  String get ocrText;

  /// No description provided for @notFound.
  ///
  /// In en, this message translates to:
  /// **'Not found'**
  String get notFound;

  /// No description provided for @needsReview.
  ///
  /// In en, this message translates to:
  /// **'Needs review'**
  String get needsReview;

  /// No description provided for @confidence.
  ///
  /// In en, this message translates to:
  /// **'Confidence {value}%'**
  String confidence(int value);

  /// No description provided for @edit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get edit;

  /// No description provided for @save.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @uploadProgress.
  ///
  /// In en, this message translates to:
  /// **'Uploading {percent}%'**
  String uploadProgress(int percent);

  /// No description provided for @errorGeneric.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong.'**
  String get errorGeneric;

  /// No description provided for @errorNetwork.
  ///
  /// In en, this message translates to:
  /// **'Cannot reach the server.'**
  String get errorNetwork;

  /// No description provided for @errorAuth.
  ///
  /// In en, this message translates to:
  /// **'Incorrect e-mail or password.'**
  String get errorAuth;

  /// No description provided for @fullName.
  ///
  /// In en, this message translates to:
  /// **'Full name'**
  String get fullName;

  /// No description provided for @arabicName.
  ///
  /// In en, this message translates to:
  /// **'Arabic name'**
  String get arabicName;

  /// No description provided for @jobTitle.
  ///
  /// In en, this message translates to:
  /// **'Job title'**
  String get jobTitle;

  /// No description provided for @company.
  ///
  /// In en, this message translates to:
  /// **'Company'**
  String get company;

  /// No description provided for @phones.
  ///
  /// In en, this message translates to:
  /// **'Phones'**
  String get phones;

  /// No description provided for @emails.
  ///
  /// In en, this message translates to:
  /// **'E-mail'**
  String get emails;

  /// No description provided for @website.
  ///
  /// In en, this message translates to:
  /// **'Website'**
  String get website;

  /// No description provided for @address.
  ///
  /// In en, this message translates to:
  /// **'Address'**
  String get address;

  /// No description provided for @offlineOcrNote.
  ///
  /// In en, this message translates to:
  /// **'This app does not run OCR on the device: recognition happens after upload.'**
  String get offlineOcrNote;

  /// No description provided for @lastError.
  ///
  /// In en, this message translates to:
  /// **'Last error: {message}'**
  String lastError(String message);

  /// No description provided for @specialty.
  ///
  /// In en, this message translates to:
  /// **'Specialty'**
  String get specialty;

  /// No description provided for @professionalDescription.
  ///
  /// In en, this message translates to:
  /// **'Professional description'**
  String get professionalDescription;

  /// No description provided for @qrDiffers.
  ///
  /// In en, this message translates to:
  /// **'The QR code differs from the printed card for: {fields}. Nothing was changed automatically.'**
  String qrDiffers(String fields);

  /// No description provided for @inferredNote.
  ///
  /// In en, this message translates to:
  /// **'Inferred, not printed on the card — please confirm'**
  String get inferredNote;

  /// No description provided for @welcome.
  ///
  /// In en, this message translates to:
  /// **'Welcome'**
  String get welcome;

  /// No description provided for @loginSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to scan and manage your business cards.'**
  String get loginSubtitle;

  /// No description provided for @advanced.
  ///
  /// In en, this message translates to:
  /// **'Advanced'**
  String get advanced;

  /// No description provided for @registrationClosed.
  ///
  /// In en, this message translates to:
  /// **'Sign-up is closed. Ask the administrator for an account.'**
  String get registrationClosed;

  /// No description provided for @totalCards.
  ///
  /// In en, this message translates to:
  /// **'Cards'**
  String get totalCards;

  /// No description provided for @toReview.
  ///
  /// In en, this message translates to:
  /// **'To review'**
  String get toReview;

  /// No description provided for @pendingSection.
  ///
  /// In en, this message translates to:
  /// **'Waiting to be sent'**
  String get pendingSection;

  /// No description provided for @myCards.
  ///
  /// In en, this message translates to:
  /// **'My cards'**
  String get myCards;

  /// No description provided for @emptyTitle.
  ///
  /// In en, this message translates to:
  /// **'No cards yet'**
  String get emptyTitle;

  /// No description provided for @emptyBody.
  ///
  /// In en, this message translates to:
  /// **'Scan your first business card: the text is read and the contact is filled in for you.'**
  String get emptyBody;

  /// No description provided for @scanCard.
  ///
  /// In en, this message translates to:
  /// **'Scan a card'**
  String get scanCard;

  /// No description provided for @copied.
  ///
  /// In en, this message translates to:
  /// **'Copied'**
  String get copied;

  /// No description provided for @deleteCard.
  ///
  /// In en, this message translates to:
  /// **'Delete this card'**
  String get deleteCard;

  /// No description provided for @deleted.
  ///
  /// In en, this message translates to:
  /// **'Card deleted'**
  String get deleted;

  /// No description provided for @refresh.
  ///
  /// In en, this message translates to:
  /// **'Refresh'**
  String get refresh;

  /// No description provided for @favorite.
  ///
  /// In en, this message translates to:
  /// **'Favourite'**
  String get favorite;

  /// No description provided for @hello.
  ///
  /// In en, this message translates to:
  /// **'Hello {name}'**
  String hello(String name);

  /// No description provided for @tapToCopy.
  ///
  /// In en, this message translates to:
  /// **'Tap a value to copy it'**
  String get tapToCopy;

  /// No description provided for @noResults.
  ///
  /// In en, this message translates to:
  /// **'No results'**
  String get noResults;

  /// No description provided for @burstTitle.
  ///
  /// In en, this message translates to:
  /// **'Camera for the PC'**
  String get burstTitle;

  /// No description provided for @burstPcAsks.
  ///
  /// In en, this message translates to:
  /// **'The PC is asking for: {side}'**
  String burstPcAsks(String side);

  /// No description provided for @burstFront.
  ///
  /// In en, this message translates to:
  /// **'the front'**
  String get burstFront;

  /// No description provided for @burstBack.
  ///
  /// In en, this message translates to:
  /// **'the back'**
  String get burstBack;

  /// No description provided for @burstShootForPc.
  ///
  /// In en, this message translates to:
  /// **'Photograph for the PC'**
  String get burstShootForPc;

  /// No description provided for @burstWaitingPc.
  ///
  /// In en, this message translates to:
  /// **'Waiting for a request from the PC…'**
  String get burstWaitingPc;

  /// No description provided for @burstWaitingPcHint.
  ///
  /// In en, this message translates to:
  /// **'On the PC, in “New”, click “Phone camera”: the request will appear here.'**
  String get burstWaitingPcHint;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en', 'fr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
    case 'fr':
      return AppLocalizationsFr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
