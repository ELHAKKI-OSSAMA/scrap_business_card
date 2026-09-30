# Model selection

## Installed and verified

| Provider | Version | Models | Languages verified | Device verified |
|---|---|---|---|---|
| PaddleOCR (paddlepaddle 3.2.2) | 3.3.3 | `PP-OCRv5_mobile_det`, `latin_PP-OCRv5_mobile_rec`, `en_PP-OCRv5_mobile_rec`, `arabic_PP-OCRv5_mobile_rec`, `PP-LCNet_x1_0_doc_ori` (~27 MB total) | Arabic, French, English, mixed — printed only, synthetic data | CPU (Windows host and Linux container) |
| Tesseract | 5.3.0 | LSTM `ara+fra+eng` | Arabic, French, English — printed only, synthetic data | CPU (container) |

"Verified" means: loads, runs, and was measured by `ml/evaluation/evaluate.py` on the
96-sample synthetic set (see [evaluation.md](evaluation.md)). No real-world dataset has been
evaluated. Weights are downloaded at image build time by
`infrastructure/scripts/download_models.py` and baked into `/opt/models` (the list of installed
models is written to `/opt/models/installed.json`); the running system makes no network calls
for models.

## Why PaddleOCR PP-OCRv5 is the default

* Measured on the same synthetic set, it beats Tesseract on every OCR and field metric
  (CER 0.0086 vs 0.1878; Arabic CER 0.0585 vs 0.2986; detection precision 0.989 vs 0.508).
* Dedicated Arabic and Latin recognisers; permissive licence (Apache-2.0); runs on CPU with
  ~1.1 s mean latency per image.
* Mobile detection model chosen for CPU; the server detection model is configured for the GPU
  override (`OCR_DET_MODEL_GPU`) but **the GPU path has not been tested**.

## Why Tesseract is kept

Fallback if Paddle fails to load (recorded on the job) and a reproducible baseline. It is faster
and lighter (0.66 s mean, 230 MB RSS vs 1033 MB) but much less accurate, especially on noisy
images (CER 0.442 on the noisy subset).

## Not included

* **Handwriting recognition** — no verified Arabic or Latin handwriting model is installed; the
  product does not claim handwriting support. Candidates to evaluate with *licensed real data*:
  TrOCR (Latin), Arabic HTR models (e.g. trained on KHATT/IFN-ENIT — check licences).
* **Cloud OCR / LLM APIs** — never required. The optional LLM enricher needs a user-supplied
  OpenAI-compatible endpoint and is off by default; it has only been tested with a mock client.
* **Machine translation** — optional endpoint, disabled by default, never automatic.

## Changing models

Set `OCR_PROVIDER`, `OCR_FALLBACK_PROVIDER`, `OCR_DET_MODEL` in `.env`; rebuild the image to bake
different weights. Re-run the evaluation before switching defaults.
