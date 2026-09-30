# Business Card Intelligence — audit (2026-09-30)

Scope: the business-card product (the only product in this repository).

## Component map

| Layer | Files |
|---|---|
| Backend product spec | `apps/api/app/products.py` (`BUSINESS_CARD`: route `business-cards`, sides front/back, exports json/csv/vcf, extractor) |
| API router | `apps/api/app/routers/documents.py` (`make_router(spec)`; card-only: `/duplicates`, `/merge`) |
| Processing | `apps/api/app/services/processing.py` (worker job; dedupe keys for cards) |
| Corrections | `apps/api/app/services/fields.py` (set / verify / append / remove, validation) |
| Database | `apps/api/app/models.py`: `documents` (product=`business_card`), `document_images`, `processing_jobs` (provider, model_metadata, timings), `ocr_regions` (immutable lines + candidate regions), `extraction_results`, `review_events`, `document_keys` (duplicates), `audit_events` |
| Schema | `packages/shared-types/shared_types/schemas.py` (`BusinessCardExtraction`, `Phone`, `QrCode`, `QrFieldCheck`), TS mirror `packages/shared-types/ts/index.ts` |
| OCR (shared) | `packages/ocr-core/ocr_core/` (PaddleOCR provider, reading order, `qr.py`) |
| Preprocessing (shared) | `packages/document-preprocessing/document_preprocessing/` |
| Extraction (card only) | `packages/extraction/extraction/business_card.py`, `business_card_lexicon.py` |
| Validation (shared) | `packages/validation/validation/` (phones, e-mail, URL, postal/country) |
| Export | `packages/extraction/extraction/export.py` (`to_vcard`, `business_row`) |
| Web | `apps/business-card-web/src/` (`App.tsx`, `components/CardFields.tsx`, `Duplicates.tsx`, `BatchUpload.tsx`) on `packages/ui` |
| Mobile | `apps/mobile/lib/src/modules/product.dart` (`ProductModule.businessCard`), shared capture/review/sync screens |
| Tests | `tests/business_card/` (fixtures, pytest suite, API suite, benchmark, harness), `apps/api/tests/test_business_card_api.py`, `apps/business-card-web/src/card.test.tsx`, `apps/mobile/test/business_card_test.dart` |

## Pipeline

upload (type sniffing, size/pixel limits, EXIF) → preprocessing (quad detection, perspective,
deskew, orientation classifier 0/90/180/270, CLAHE, denoise only when noisy) → PaddleOCR
detection + per-line Latin/Arabic recognition → skew-aware reading order (LTR/RTL blocks) →
language per line → QR decoding (OpenCV) → card extraction (below) → validation → confidence →
review → corrections → export. The original image is always kept; the processed image is stored
separately.

Extraction layers in `business_card.py`: deterministic contact parsing (e-mail, URL, LinkedIn,
handles, phones with printed labels) → address block → professional description → titles
(shared lexicon + card-only additions) → name ranking by text size/position (the first line is not
assumed to be the name) → Arabic name → company (marker or e-mail/website domain) → explicit
specialty → inferred doctor title (flagged) → qualifications → logo candidate → phone country from
the printed address → OCR l/I fix in Roman numerals of the street → QR cross-check → review list.
No NER model and no LLM are used by default (optional grounded LLM enrichment exists, off).

## Changes made in this audit

| Problem found (real output) | Change |
|---|---|
| Specialty on the medical card not found | Explicit specialty terms (fr/en/ar) → `specialty` with canonical `normalized_value`; nothing mapped from free descriptions |
| "Spécialiste des maladies du foie …" lost | New `professional_description` field (verbatim) |
| No job title on "Dr … + specialty" cards | `job_title` "Médecin"/"Doctor"/"طبيب" **inferred**, confidence ≤ 0.5, always `needs_review`, not exported to vCard until confirmed |
| "Chief Executive Officer" not a title | Card-only title additions |
| Logo missed; OCR read it as "0" | Tiny OCR "lines" ignored when locating the logo |
| Partly hidden e-mail fragment became the website | Explicit `www`/`https` URLs win; bare-domain fragments flagged `possible_fragment_of` + warning |
| Local numbers never normalised even with "Maroc" printed | Country taken from the card's own printed address (`region_inferred_from="card_address"`, needs review); never from language or city alone |
| "Hassan II" read as "Hassan ll" | Structured `street` corrected; `original_text` unchanged; warning recorded |
| QR vs OCR conflicts not shown | `qr_checks` (match / conflict / qr_only); conflicts send the OCR field to review; nothing imported automatically |
| No list of fields needing review | `review_fields`, recomputed after every correction; `qr_checks`/`review_fields` read-only |
| vCard exported inferred values | Inferred values excluded unless verified/corrected; specialty and description in NOTE |
| CSV lacked typed phones | `mobile`, `telephone`, `fax`, `street`, `professional_description`, `qualifications` columns |
| Web review lacked normalized value / source region / QR comparison / description | Added (opt-in `details` on the shared `FieldRow`) |
| Mobile review lacked specialty / description / QR notice | Added |

Not a product bug: OpenCV 4.10's QR **encoder** generates invalid symbols above ~version 7; the
product's **decoder** reads valid vCard QR codes. Fixtures now generate QR with `zxing-cpp`
(test-data dependency only).

## Status

| Area | Status | Evidence |
|---|---|---|
| OCR engine | VERIFIED | PaddleOCR 3.3.3 / paddlepaddle 3.2.2 CPU; `PP-OCRv5_mobile_det`, `latin_`, `en_`, `arabic_PP-OCRv5_mobile_rec`, `PP-LCNet_x1_0_doc_ori` |
| Arabic (printed) | VERIFIED on synthetic cards; PARTIALLY SUPPORTED overall | names, titles, company, address read verbatim; RTL lines; digits inside Arabic lines and Eastern Arabic-Indic digits are weak (evaluation CER Arabic 0.058) |
| French | VERIFIED (synthetic) | accents, apostrophes (’ and '), hyphens, titles preserved |
| English | VERIFIED (synthetic) | names, titles, URLs, e-mails preserved |
| Mixed ar+fr, ar+en, fr+en, ar+fr+en | VERIFIED (synthetic) | per-line recogniser choice |
| Portrait / landscape / rotated 7° / rotated 90° / front+back / low-res+noise | VERIFIED (synthetic) | |
| Partially unreadable card | VERIFIED: nothing invented, fragments flagged | |
| QR (detect, decode, classify vCard/MECARD/URL/tel/email/text, compare, user-driven import) | VERIFIED (synthetic vCard) | never opened/executed |
| Logo candidate | VERIFIED on one synthetic colour logo; heuristic | |
| Icons (phone/e-mail pictograms as context) | NOT IMPLEMENTED | phone/e-mail typing uses printed labels only |
| NER model | NOT IMPLEMENTED (rules + layout) | |
| Web | VERIFIED (unit tests, Docker UI in fr) | |
| Flutter | VERIFIED (analyze, 24 tests incl. 5 card tests, debug APK); on-device camera/scanner NOT VERIFIED | |
| Docker | VERIFIED | full card suite through the gateway, real worker OCR |
| Database / isolation | VERIFIED | other workspace 404 for document, image, export |
| Exports JSON / CSV / vCard | VERIFIED | Arabic preserved, formula injection neutralised |
| Real photographed cards | BLOCKED | the user's medical card photo is not in the repository |

## Running

```bash
pytest tests/business_card                               # real OCR on synthetic cards (~30 s)
python tests/business_card/harness.py D K --save out/    # inspect raw OCR + extraction per card
python tests/business_card/benchmark.py                  # latency / memory → ml/evaluation/reports/
python tests/business_card/api_suite.py                  # against the running Docker stack
pytest apps/api/tests/test_business_card_api.py
npm test -w apps/business-card-web
cd apps/mobile && flutter test test/business_card_test.dart
```

To test a real card photo: `python tests/business_card/harness.py` works on fixtures; for an
arbitrary image upload it through the web app or `POST /api/v1/business-cards/{id}/images`.
