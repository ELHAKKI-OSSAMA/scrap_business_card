# Evaluation report – ollama

> **SYNTHETIC DATA ONLY – not representative of real-world accuracy**

Generated 2026-10-02T17:24:39.135337+00:00 · samples: 108 · failures: 0

## OCR (line level)

| Group | Lines | CER | WER | Line accuracy |
|---|---:|---:|---:|---:|
| ALL | 1116 | 0.0001 | 0.0003 | 0.9991 |
| lang=ar | 144 | 0.0011 | 0.003 | 0.9931 |
| lang=en | 306 | 0.0 | 0.0 | 1.0 |
| lang=fr | 450 | 0.0 | 0.0 | 1.0 |
| lang=und | 216 | 0.0 | 0.0 | 1.0 |
| product=business_card | 1116 | 0.0001 | 0.0003 | 0.9991 |
| quality=clean | 186 | 0.0 | 0.0 | 1.0 |
| quality=faded | 186 | 0.0 | 0.0 | 1.0 |
| quality=low_res | 186 | 0.0 | 0.0 | 1.0 |
| quality=noisy | 186 | 0.0 | 0.0 | 1.0 |
| quality=photo | 186 | 0.0006 | 0.0017 | 0.9946 |
| quality=rotated | 186 | 0.0 | 0.0 | 1.0 |
| script=Arab | 144 | 0.0011 | 0.003 | 0.9931 |
| script=Latn | 972 | 0.0 | 0.0 | 1.0 |
| type=printed | 1116 | 0.0001 | 0.0003 | 0.9991 |

Detection recall (GT lines matched at CER ≤ 0.6): **1.0**, precision: **1.0**

## Extraction – exact match per field

| Field / group | N | Exact match | Missing |
|---|---:|---:|---:|
| address.city | 90 | 1.0 | 0 |
| address.country | 108 | 1.0 | 0 |
| address.postal_code | 108 | 1.0 | 0 |
| arabic_name | 54 | 1.0 | 0 |
| company | 108 | 1.0 | 0 |
| first_name | 90 | 1.0 | 0 |
| full_name | 108 | 1.0 | 0 |
| industry | 108 | 1.0 | 0 |
| job_title | 108 | 0.9907 | 0 |
| last_name | 90 | 1.0 | 0 |
| phone_type | 216 | 1.0 | 0 |
| website | 108 | 1.0 | 0 |

## Entities (P / R / F1)

| Entity | P | R | F1 |
|---|---:|---:|---:|
| email|ALL | 1.0 | 1.0 | 1.0 |
| email|lang=ar | 1.0 | 1.0 | 1.0 |
| email|lang=ar_en | 1.0 | 1.0 | 1.0 |
| email|lang=ar_fr | 1.0 | 1.0 | 1.0 |
| email|lang=en | 1.0 | 1.0 | 1.0 |
| email|lang=fr | 1.0 | 1.0 | 1.0 |
| email|lang=fr_en | 1.0 | 1.0 | 1.0 |
| email|quality=clean | 1.0 | 1.0 | 1.0 |
| email|quality=faded | 1.0 | 1.0 | 1.0 |
| email|quality=low_res | 1.0 | 1.0 | 1.0 |
| email|quality=noisy | 1.0 | 1.0 | 1.0 |
| email|quality=photo | 1.0 | 1.0 | 1.0 |
| email|quality=rotated | 1.0 | 1.0 | 1.0 |
| phone|ALL | 1.0 | 1.0 | 1.0 |
| phone|lang=ar | 1.0 | 1.0 | 1.0 |
| phone|lang=ar_en | 1.0 | 1.0 | 1.0 |
| phone|lang=ar_fr | 1.0 | 1.0 | 1.0 |
| phone|lang=en | 1.0 | 1.0 | 1.0 |
| phone|lang=fr | 1.0 | 1.0 | 1.0 |
| phone|lang=fr_en | 1.0 | 1.0 | 1.0 |
| phone|quality=clean | 1.0 | 1.0 | 1.0 |
| phone|quality=faded | 1.0 | 1.0 | 1.0 |
| phone|quality=low_res | 1.0 | 1.0 | 1.0 |
| phone|quality=noisy | 1.0 | 1.0 | 1.0 |
| phone|quality=photo | 1.0 | 1.0 | 1.0 |
| phone|quality=rotated | 1.0 | 1.0 | 1.0 |

## Confidence calibration (field confidence vs. exact match)

| Confidence | N | Accuracy |
|---|---:|---:|

## System

- images: 108, mean latency 3.635 s (p50 3.269, p95 6.116), throughput ≈ 16.5 img/min (single process, 12 logical CPUs)
- peak RSS: 90 MB · failure rate: 0.0
- environment: Windows-11-10.0.26200-SP0, Python 3.12.11

## Per-group field detail

| Field | Group | N | Exact |
|---|---|---:|---:|
| address.city | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar|quality=photo|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=rotated|type=printed | 3 | 1.0 |
