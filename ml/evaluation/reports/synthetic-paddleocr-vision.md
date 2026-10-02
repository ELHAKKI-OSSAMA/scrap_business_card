# Evaluation report – paddleocr+vision:gemma4:31b

> **SYNTHETIC DATA ONLY – not representative of real-world accuracy**

Generated 2026-10-02T17:18:00.733939+00:00 · samples: 108 · failures: 0

## OCR (line level)

| Group | Lines | CER | WER | Line accuracy |
|---|---:|---:|---:|---:|
| ALL | 1116 | 0.0075 | 0.0197 | 0.9516 |
| lang=ar | 144 | 0.0726 | 0.1548 | 0.7431 |
| lang=en | 306 | 0.0008 | 0.0037 | 0.9869 |
| lang=fr | 450 | 0.0004 | 0.0016 | 0.9933 |
| lang=und | 216 | 0.0019 | 0.0463 | 0.9537 |
| product=business_card | 1116 | 0.0075 | 0.0197 | 0.9516 |
| quality=clean | 186 | 0.0071 | 0.0205 | 0.9624 |
| quality=faded | 186 | 0.0021 | 0.0068 | 0.9839 |
| quality=low_res | 186 | 0.0151 | 0.0479 | 0.8978 |
| quality=noisy | 186 | 0.0089 | 0.0154 | 0.9516 |
| quality=photo | 186 | 0.0044 | 0.0103 | 0.9677 |
| quality=rotated | 186 | 0.0077 | 0.0171 | 0.9462 |
| script=Arab | 144 | 0.0726 | 0.1548 | 0.7431 |
| script=Latn | 972 | 0.0009 | 0.0054 | 0.9825 |
| type=printed | 1116 | 0.0075 | 0.0197 | 0.9516 |

Detection recall (GT lines matched at CER ≤ 0.6): **0.9991**, precision: **0.9991**

## Extraction – exact match per field

| Field / group | N | Exact match | Missing |
|---|---:|---:|---:|
| address.city | 90 | 1.0 | 0 |
| address.country | 108 | 0.9815 | 2 |
| address.postal_code | 108 | 0.8796 | 12 |
| arabic_name | 54 | 0.963 | 0 |
| company | 108 | 0.9074 | 0 |
| first_name | 90 | 1.0 | 0 |
| full_name | 108 | 1.0 | 0 |
| industry | 108 | 0.9907 | 1 |
| job_title | 108 | 0.9722 | 2 |
| last_name | 90 | 1.0 | 0 |
| phone_type | 216 | 1.0 | 0 |
| website | 108 | 1.0 | 0 |

## Entities (P / R / F1)

| Entity | P | R | F1 |
|---|---:|---:|---:|
| email|ALL | 0.9074 | 0.9074 | 0.9074 |
| email|lang=ar | 0.9444 | 0.9444 | 0.9444 |
| email|lang=ar_en | 0.8889 | 0.8889 | 0.8889 |
| email|lang=ar_fr | 1.0 | 1.0 | 1.0 |
| email|lang=en | 0.6111 | 0.6111 | 0.6111 |
| email|lang=fr | 1.0 | 1.0 | 1.0 |
| email|lang=fr_en | 1.0 | 1.0 | 1.0 |
| email|quality=clean | 0.8889 | 0.8889 | 0.8889 |
| email|quality=faded | 1.0 | 1.0 | 1.0 |
| email|quality=low_res | 0.7778 | 0.7778 | 0.7778 |
| email|quality=noisy | 0.8889 | 0.8889 | 0.8889 |
| email|quality=photo | 0.8889 | 0.8889 | 0.8889 |
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
| 0.5-0.6 | 342 | 0.994 |
| 0.7-0.8 | 95 | 0.884 |
| 0.8-0.9 | 226 | 1.0 |
| 0.9-1.0 | 108 | 1.0 |

## System

- images: 108, mean latency 1.877 s (p50 1.577, p95 2.752), throughput ≈ 32.0 img/min (single process, 12 logical CPUs)
- peak RSS: 1029 MB · failure rate: 0.0
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
| address.country | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.3333 |
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
| address.postal_code | business_card|lang=ar|quality=clean|type=printed | 3 | 0.0 |
| address.postal_code | business_card|lang=ar|quality=faded|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.0 |
| address.postal_code | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| address.postal_code | business_card|lang=ar|quality=photo|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.3333 |
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
| arabic_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 0.6667 |
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
| arabic_name | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.6667 |
| arabic_name | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.3333 |
| company | business_card|lang=ar|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.6667 |
| company | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=noisy|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.6667 |
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
| industry | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.6667 |
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
| job_title | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.3333 |
| job_title | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
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
