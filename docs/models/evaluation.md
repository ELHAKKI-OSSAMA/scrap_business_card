# Evaluation

> **Synthetic data only — not representative of real-world accuracy.**
> All numbers come from computer-rendered business cards produced by
> `ml/datasets/synthetic/generate.py`. They show that the pipeline works end to end and allow
> comparing providers; they do **not** predict accuracy on real photographed cards.
> Real photographs are evaluated separately with `tests/business_card/real_world/evaluate.py`
> against a hand-verified ground truth.

## Dataset

108 synthetic business cards with ground-truth annotations:

* Languages: Arabic, French, English and mixed ar/fr, ar/en, fr/en (3 cards per combination).
* Quality variants per card: clean, faded, low_res, noisy, photo (perspective + lighting), rotated.

Each sample's `annotation.json` carries `source: synthetic` and its licence.

## Running

```bash
python ml/datasets/synthetic/generate.py                       # writes ml/datasets/synthetic/out
python ml/evaluation/evaluate.py --provider paddleocr          # or --provider tesseract
python ml/evaluation/evaluate.py --provider paddleocr --vision # + Gemma 4 field merge (Ollama)
python ml/evaluation/evaluate.py --provider ollama             # cloud-only: Gemma 4 reads + extracts
```

Tesseract runs inside the container (it is installed there):

```bash
docker compose run --rm --no-deps -w /srv -v "$PWD/ml:/srv/ml" worker python ml/evaluation/evaluate.py --provider tesseract
```

Reports: `ml/evaluation/reports/synthetic-<provider>.{json,md}` — metrics by language, quality and
field, confidence calibration, latency and memory.

## Results (2026-09-30)

PaddleOCR: Windows 11 host, CPU. Tesseract: Linux container, CPU. 108 cards, 0 failures each.

### Text recognition

| Subset | PaddleOCR CER | PaddleOCR line acc. | Tesseract CER | Tesseract line acc. |
|---|---|---|---|---|
| All | **0.0075** | 0.952 | 0.1745 | 0.685 |
| Arabic | **0.0726** | 0.743 | 0.3237 | 0.549 |
| French | **0.0004** | 0.993 | 0.1312 | 0.727 |
| English | **0.0008** | 0.987 | 0.1763 | 0.732 |
| Noisy images | 0.0089 | 0.952 | 0.3483 | 0.591 |

Detection: PaddleOCR recall 0.999 / precision 0.999; Tesseract 0.868 / 0.407.

### Fields (exact match)

| Field | n | PaddleOCR | Tesseract |
|---|---|---|---|
| full_name | 108 | 1.0 | 0.778 |
| first_name / last_name | 90 | 1.0 / 1.0 | 0.811 / 0.811 |
| arabic_name | 54 | 0.963 | 0.704 |
| job_title | 108 | 0.972 | 0.778 |
| company | 108 | 0.907 | 0.565 |
| industry | 108 | 0.991 | 0.815 |
| website | 108 | 1.0 | 0.713 |
| address.postal_code | 108 | 0.880 | 0.843 |
| address.city | 90 | 1.0 | 0.900 |
| address.country | 108 | 0.981 | 0.796 |
| phone type | 216 / 148 | 1.0 | 0.993 |

Entities: phones F1 1.0 (PaddleOCR) vs 0.811; e-mails F1 0.907 vs 0.628.

### System

| | PaddleOCR | Tesseract |
|---|---|---|
| Mean latency / image | 2.15 s* | 0.84 s |
| p95 latency | 3.47 s* | 0.97 s |
| Peak RSS | 1026 MB | 183 MB |

\* measured while a Docker image build was running on the same machine; an earlier run without
concurrent load measured ~1.1 s mean. `tests/business_card/benchmark.py` measures latency on an
idle machine (≈1.0 s per card after warm-up).

### Calibration

PaddleOCR field confidences are under-confident (0.5–0.6 bucket: 99.4 % correct; 0.9–1.0:
100 %). Thresholds for `needs_review` are therefore conservative.

## Gemma 4 via Ollama Cloud (2026-10-02)

Same 108 cards, `gemma4:31b` on Ollama Cloud. Reports: `synthetic-paddleocr-vision.*`,
`synthetic-ollama.*`.

| Field / metric | PaddleOCR + rules | + Gemma merge (`--vision`) | **Ollama only (`--provider ollama`)** |
|---|---|---|---|
| OCR CER all / Arabic | 0.0075 / 0.0726 | (same OCR) | **0.0001 / 0.0011** |
| OCR line accuracy all / Arabic | 0.952 / 0.743 | (same OCR) | **0.999 / 0.993** |
| company | 0.907 | 0.907 | **1.000** |
| address.postal_code | 0.880 | 0.880 | **1.000** |
| address.country | 0.982 | 0.982 | **1.000** |
| arabic_name | 0.963 | 0.963 | **1.000** |
| job_title | 0.972 | 0.972 | 0.991 |
| e-mail F1 | 0.907 | 0.907 | **1.000** |
| full_name, first/last name, city, website, phones, phone type | 1.000 | 1.000 | 1.000 |
| latency / card side | 2.15 s (local CPU) | +2.0 s | 3.6 s mean, p95 6.1 s (network) |

Why the merge mode gains nothing: Gemma's values are accepted only when they occur in the
PaddleOCR text, so where PaddleOCR misread, Gemma's correct value is (by design) rejected. In
cloud-only mode the grounding text is Gemma's own transcription. The first `--vision` run
reached 0.667 on `full_name` because Gemma kept honorifics ("Pr.", "Me"); the merge now strips
them like the rules do — numbers above are after that fix.

Cloud-only mode has no confidence scores (`null`), approximate line boxes, no QR/logo detection,
and sends images to Ollama Cloud. On the one real photographed card tested (Omnishore, not in the
repository) it extracted every printed field except the postal code.

## Known weaknesses surfaced by evaluation

* Arabic lines: 26 % not exact, mostly digit runs dropped by the Arabic recogniser
  (mitigated by flags and reduced address confidence, not fixed).
* Postal codes on Arabic-script lines (0.880).
* Company names without a marker word (0.907).

## What is still needed

A real, licensed, consented evaluation set of photographed business cards (Arabic, French,
English, mixed). Collecting or licensing such data is a decision for the project owner.
