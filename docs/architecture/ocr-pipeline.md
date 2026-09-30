# OCR pipeline

Implemented in `packages/ocr-core/ocr_core/engine.py` (`OcrEngine`) and the packages it calls.
Everything below runs locally; no external service is required.

## 1. Validation and preprocessing (`document-preprocessing`)

* **Validation** (`validation.py`): content sniffing (JPEG, PNG, WebP, TIFF by magic bytes, not
  extension), max size, decompression-bomb pixel limit, EXIF orientation applied then stripped.
* **Quality** (`quality.py`): blur (Laplacian variance), darkness, low contrast and low
  resolution warnings (no glare detection) — reported to the user, not used to reject.
* **Geometry** (`geometry.py`): document quad detection → perspective correction; deskew; page
  orientation by the `PP-LCNet_x1_0_doc_ori` classifier (0/90/180/270).
* **Enhancement** (`enhance.py`): CLAHE contrast and non-local-means denoise (only when noise is detected) on the OCR copy only; the original is kept.
* **Regions** (`regions.py`): colour patches (logo candidates).

## 2. Text detection and recognition (`ocr-core`)

Provider interface in `base.py`; providers in `paddle_provider.py` and `tesseract_provider.py`;
selection in `selection.py` / `registry.py`.

**PaddleOCR 3.3.3 (default)**

| Stage | Model |
|---|---|
| Detection | `PP-OCRv5_mobile_det` (`PP-OCRv5_server_det` configured for the GPU worker; not tested) |
| Recognition, French/English | `latin_PP-OCRv5_mobile_rec` |
| Recognition, English | `en_PP-OCRv5_mobile_rec` |
| Recognition, Arabic | `arabic_PP-OCRv5_mobile_rec` |
| Orientation | `PP-LCNet_x1_0_doc_ori` |

Each detected line is recognised by the Latin **and** Arabic recognisers and
`choose_hypothesis` keeps the better one using script evidence and confidence (the Latin model
outputs blanks on Arabic crops; the Arabic model can read some Latin). Mixed documents are
therefore handled per line, not per page.

Known model behaviour and mitigations:

* The Arabic recogniser drops or garbles digit runs. Affected lines are flagged
  `digits_possibly_dropped`; a conservative segmentation-based digit repair runs; address fields
  depending on uncertain digits get halved confidence and `needs_review`.
* Eastern Arabic-Indic digits (٠-٩) are recognised poorly.
* Paddle predictors are not thread-safe → inference is serialised with a lock (`_infer_lock`);
  a regression test covers concurrent calls. Scale by worker processes, not threads.

**Tesseract 5.3 (`ara+fra+eng`)** — fallback when Paddle is unavailable and the evaluation
baseline. The provider used is recorded on each job.

**Handwriting**: no verified handwriting recogniser is installed. `/api/v1/models` reports
`handwriting: available=false`; handwritten text is read best-effort by the printed models.

## 3. Reading order (`reading_order.py`)

Skew-aware: the median polygon angle de-rotates line boxes; lines are grouped into blocks by
union-find on proximity, blocks into bands, and bands are ordered LTR or RTL according to the
dominant script of the block.

## 4. Language detection and normalisation (`language-detection`)

Per-line script detection (Arabic / Latin / digits) and fr/en classification; document summary via
`summarize_languages`. `normalize_display` unifies Persian yeh/keheh with Arabic forms;
`normalize_search` builds diacritic-insensitive search text; `digits_to_ascii` maps Arabic-Indic
digits for validation only. **No translation is performed automatically** (optional
`/translate` endpoint, disabled by default, never overwrites OCR text).

## 5. Extraction (`extraction`)

Rule-based, per product, every value linked to the source line ids (`source_region_ids`) and
the method used.

* **Business card** (`business_card.py`): name (Latin and Arabic), job title (≤8 words, ≤60
  chars), company (lexicon markers), phones (typed: mobile/fixed/fax), emails, websites,
  addresses, social handles, QR codes (decoded, URL checked by `is_safe_url`, **never opened**).
  Duplicate keys (email, E.164 phone, normalised name+company) are stored for suggestions;
  merging is always a user action.
* **Optional LLM enrichment** (`llm.py`, off by default): OpenAI-compatible endpoint, strict JSON
  schema, every value must be grounded in OCR text, and document lines that look like
  instructions (prompt injection) are rejected.

## 6. Validation and confidence (`validation`)

Phones via `phonenumbers` (E.164, type), email syntax, URLs, dates (multiple formats, plausible
range), postal codes per country. Field confidence =
`ocr_confidence × method_reliability × validation_factor`; `None` when there is no evidence.
Fields below threshold or with warnings get `review_status = needs_review`.

Calibration on synthetic data shows scores are **under-confident** (e.g. bucket 0.5–0.6 is 97.8 %
correct for PaddleOCR); treat them as ranking signals, not probabilities.

## 7. Persistence

Raw OCR pages/lines/regions and machine extraction are stored immutably per job; the reviewable
`data` starts as a copy. Corrections append `review_events`. Re-processing creates a new job and
never discards user-verified values silently.
