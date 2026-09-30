# Real-world business-card validation

Put **real photographs only** here (never synthetic renders).

```
tests/business_card/real_world/medical_card/
    front.jpg            # required (jpg / jpeg / png / webp / tif)
    back.jpg             # optional
    ground_truth.json    # copy ground_truth.template.json and fill it in BY HAND from the physical card
```

Images and `ground_truth.json` in this folder are git-ignored (personal data).

## Ground truth rules

* Type exactly what is printed (accents, apostrophes, Arabic letters, dots in phone numbers).
* Leave a field `null` if it is not printed on the card. Do not infer (no city if no city is printed).
* `lines` lists every printed line, one entry per line, with its language (`ar`, `fr`, `en`, `digits`).
  It is used for character error rate (CER); keep it in the card's reading order.
* Set `"verified_by"` to your name once you have checked it against the physical card.

## Run

```bash
python tests/business_card/real_world/evaluate.py medical_card            # OCR + extraction + comparison
python tests/business_card/real_world/evaluate.py medical_card --api       # + save / correct / retrieve / export through the running stack
```

Outputs go to `tests/business_card/real_world/medical_card/out/` (raw OCR, extracted JSON, comparison
report). The production pipeline is used unchanged (`OcrEngine(PaddleProvider())` + `extract_business_card`,
the same calls the worker makes).
