// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for French (`fr`).
class AppLocalizationsFr extends AppLocalizations {
  AppLocalizationsFr([String locale = 'fr']) : super(locale);

  @override
  String get appTitle => 'Scanner de cartes de visite';

  @override
  String get cardScanner => 'Scanner de cartes de visite';

  @override
  String get newScan => 'Nouvelle numérisation';

  @override
  String get front => 'Recto';

  @override
  String get back => 'Verso';

  @override
  String get optional => 'facultatif';

  @override
  String get scanDocument => 'Numériser (recadrage auto)';

  @override
  String get camera => 'Appareil photo';

  @override
  String get gallery => 'Galerie';

  @override
  String get crop => 'Recadrer et pivoter';

  @override
  String get retake => 'Reprendre';

  @override
  String get remove => 'Retirer';

  @override
  String get saveDraft => 'Enregistrer le brouillon';

  @override
  String get submit => 'Enregistrer et traiter';

  @override
  String get title => 'Titre (facultatif)';

  @override
  String get search => 'Rechercher dans les brouillons…';

  @override
  String get noDrafts =>
      'Aucune numérisation. Touchez + pour capturer un document.';

  @override
  String get statusLocalDraft => 'Brouillon local';

  @override
  String get statusPendingUpload => 'Envoi en attente';

  @override
  String get statusProcessing => 'Traitement';

  @override
  String get statusCompleted => 'Terminé';

  @override
  String get statusFailed => 'Échec';

  @override
  String get offlineBanner =>
      'Hors ligne — les brouillons sont enregistrés sur l’appareil et envoyés au retour de la connexion. L’OCR s’exécute sur le serveur.';

  @override
  String get syncNow => 'Synchroniser';

  @override
  String get syncing => 'Synchronisation…';

  @override
  String get settings => 'Paramètres';

  @override
  String get language => 'Langue';

  @override
  String get server => 'URL du serveur';

  @override
  String get signIn => 'Se connecter';

  @override
  String get signOut => 'Se déconnecter';

  @override
  String get email => 'E-mail';

  @override
  String get password => 'Mot de passe';

  @override
  String get register => 'Créer un compte';

  @override
  String signedInAs(String email) {
    return 'Connecté en tant que $email';
  }

  @override
  String get notSignedIn =>
      'Non connecté. Les brouillons restent sur l’appareil jusqu’à la connexion.';

  @override
  String get needImage => 'Ajoutez au moins l’image du recto.';

  @override
  String get delete => 'Supprimer';

  @override
  String get deleteConfirm =>
      'Supprimer ce brouillon et ses images de l’appareil ?';

  @override
  String get cancel => 'Annuler';

  @override
  String get extracted => 'Champs extraits';

  @override
  String get ocrText => 'Texte reconnu';

  @override
  String get notFound => 'Non trouvé';

  @override
  String get needsReview => 'À vérifier';

  @override
  String confidence(int value) {
    return 'Confiance $value %';
  }

  @override
  String get edit => 'Modifier';

  @override
  String get save => 'Enregistrer';

  @override
  String get retry => 'Réessayer';

  @override
  String uploadProgress(int percent) {
    return 'Envoi $percent %';
  }

  @override
  String get errorGeneric => 'Une erreur s’est produite.';

  @override
  String get errorNetwork => 'Serveur injoignable.';

  @override
  String get errorAuth => 'E-mail ou mot de passe incorrect.';

  @override
  String get fullName => 'Nom complet';

  @override
  String get arabicName => 'Nom en arabe';

  @override
  String get jobTitle => 'Fonction';

  @override
  String get company => 'Société';

  @override
  String get phones => 'Téléphones';

  @override
  String get emails => 'E-mail';

  @override
  String get website => 'Site web';

  @override
  String get address => 'Adresse';

  @override
  String get offlineOcrNote =>
      'Cette application n’effectue pas l’OCR sur l’appareil : la reconnaissance a lieu après l’envoi.';

  @override
  String lastError(String message) {
    return 'Dernière erreur : $message';
  }

  @override
  String get specialty => 'Spécialité';

  @override
  String get professionalDescription => 'Description professionnelle';

  @override
  String qrDiffers(String fields) {
    return 'Le QR code diffère de la carte imprimée pour : $fields. Rien n’a été modifié automatiquement.';
  }

  @override
  String get inferredNote => 'Déduit, non imprimé sur la carte — à confirmer';

  @override
  String get welcome => 'Bienvenue';

  @override
  String get loginSubtitle =>
      'Connectez-vous pour scanner et gérer vos cartes de visite.';

  @override
  String get advanced => 'Avancé';

  @override
  String get registrationClosed =>
      'Les inscriptions sont fermées. Demandez un compte à l’administrateur.';

  @override
  String get totalCards => 'Cartes';

  @override
  String get toReview => 'À vérifier';

  @override
  String get pendingSection => 'En attente d’envoi';

  @override
  String get myCards => 'Mes cartes';

  @override
  String get emptyTitle => 'Aucune carte pour l’instant';

  @override
  String get emptyBody =>
      'Scannez votre première carte de visite : le texte est lu et le contact est rempli pour vous.';

  @override
  String get scanCard => 'Scanner une carte';

  @override
  String get copied => 'Copié';

  @override
  String get deleteCard => 'Supprimer cette carte';

  @override
  String get deleted => 'Carte supprimée';

  @override
  String get refresh => 'Actualiser';

  @override
  String get favorite => 'Favori';

  @override
  String hello(String name) {
    return 'Bonjour $name';
  }

  @override
  String get tapToCopy => 'Touchez une valeur pour la copier';

  @override
  String get noResults => 'Aucun résultat';

  @override
  String get burstTitle => 'Caméra pour le PC';

  @override
  String get burstHint =>
      'Photographiez les cartes à la chaîne : chaque carte part tout de suite et s’affiche en direct sur votre PC (site web → « Caméra téléphone », même compte).';

  @override
  String get burstShoot => 'Photographier une carte';

  @override
  String get burstFrontReady => 'Recto pris';

  @override
  String get burstSendNow => 'Envoyer (recto seul)';

  @override
  String get burstAddBack => 'Ajouter le verso puis envoyer';

  @override
  String get burstRetake => 'Reprendre';

  @override
  String burstCardN(int n) {
    return 'Carte $n';
  }

  @override
  String get burstDone => 'Analysée — visible sur le PC';

  @override
  String get burstFailed => 'Échec';

  @override
  String get burstProcessing => 'Analyse en cours…';

  @override
  String get burstSending => 'Envoi…';

  @override
  String burstPcAsks(String side) {
    return 'Le PC demande : $side';
  }

  @override
  String get burstFront => 'le recto';

  @override
  String get burstBack => 'le verso';

  @override
  String get burstShootForPc => 'Photographier pour le PC';
}
