# Evaluation report – tesseract

> **SYNTHETIC DATA ONLY – not representative of real-world accuracy**

Generated 2026-09-30T21:40:20.445916+00:00 · samples: 108 · failures: 0

## OCR (line level)

| Group | Lines | CER | WER | Line accuracy |
|---|---:|---:|---:|---:|
| ALL | 1116 | 0.1745 | 0.2362 | 0.6846 |
| lang=ar | 144 | 0.3237 | 0.381 | 0.5486 |
| lang=en | 306 | 0.1763 | 0.2231 | 0.732 |
| lang=fr | 450 | 0.1312 | 0.1922 | 0.7267 |
| lang=und | 216 | 0.1859 | 0.4583 | 0.6204 |
| product=business_card | 1116 | 0.1745 | 0.2362 | 0.6846 |
| quality=clean | 186 | 0.0148 | 0.0342 | 0.914 |
| quality=faded | 186 | 0.0304 | 0.0889 | 0.871 |
| quality=low_res | 186 | 0.0718 | 0.159 | 0.6237 |
| quality=noisy | 186 | 0.3483 | 0.3949 | 0.5914 |
| quality=photo | 186 | 0.0047 | 0.0274 | 0.914 |
| quality=rotated | 186 | 0.5773 | 0.7128 | 0.1935 |
| script=Arab | 144 | 0.3237 | 0.381 | 0.5486 |
| script=Latn | 972 | 0.1594 | 0.2209 | 0.7047 |
| type=printed | 1116 | 0.1745 | 0.2362 | 0.6846 |

Detection recall (GT lines matched at CER ≤ 0.6): **0.8683**, precision: **0.4068**

## Extraction – exact match per field

| Field / group | N | Exact match | Missing |
|---|---:|---:|---:|
| address.city | 90 | 0.9 | 8 |
| address.country | 108 | 0.7963 | 21 |
| address.postal_code | 108 | 0.8426 | 14 |
| arabic_name | 54 | 0.7037 | 12 |
| company | 108 | 0.5648 | 16 |
| first_name | 90 | 0.8111 | 15 |
| full_name | 108 | 0.7778 | 19 |
| industry | 108 | 0.8148 | 15 |
| job_title | 108 | 0.7778 | 18 |
| last_name | 90 | 0.8111 | 15 |
| phone_type | 148 | 0.9932 | 0 |
| website | 108 | 0.713 | 16 |

## Entities (P / R / F1)

| Entity | P | R | F1 |
|---|---:|---:|---:|
| email|ALL | 0.7229 | 0.5556 | 0.6283 |
| email|lang=ar | 0.9167 | 0.6111 | 0.7333 |
| email|lang=ar_en | 0.5714 | 0.4444 | 0.5 |
| email|lang=ar_fr | 0.8667 | 0.7222 | 0.7879 |
| email|lang=en | 0.3077 | 0.2222 | 0.2581 |
| email|lang=fr | 0.8571 | 0.6667 | 0.75 |
| email|lang=fr_en | 0.8 | 0.6667 | 0.7273 |
| email|quality=clean | 0.8333 | 0.8333 | 0.8333 |
| email|quality=faded | 0.8333 | 0.8333 | 0.8333 |
| email|quality=low_res | 0.2778 | 0.2778 | 0.2778 |
| email|quality=noisy | 0.8182 | 0.5 | 0.6207 |
| email|quality=photo | 0.8889 | 0.8889 | 0.8889 |
| email|quality=rotated | None | 0.0 | None |
| phone|ALL | 0.9933 | 0.6852 | 0.811 |
| phone|lang=ar | 1.0 | 0.3611 | 0.5306 |
| phone|lang=ar_en | 1.0 | 0.75 | 0.8571 |
| phone|lang=ar_fr | 0.9667 | 0.8056 | 0.8788 |
| phone|lang=en | 1.0 | 0.6944 | 0.8197 |
| phone|lang=fr | 1.0 | 0.7222 | 0.8387 |
| phone|lang=fr_en | 1.0 | 0.7778 | 0.875 |
| phone|quality=clean | 1.0 | 0.8889 | 0.9412 |
| phone|quality=faded | 1.0 | 0.9444 | 0.9714 |
| phone|quality=low_res | 1.0 | 0.8333 | 0.9091 |
| phone|quality=noisy | 1.0 | 0.6111 | 0.7586 |
| phone|quality=photo | 1.0 | 0.8333 | 0.9091 |
| phone|quality=rotated | 0.0 | 0.0 | None |

## Confidence calibration (field confidence vs. exact match)

| Confidence | N | Accuracy |
|---|---:|---:|
| 0.1-0.2 | 1 | 0.0 |
| 0.2-0.3 | 4 | 0.0 |
| 0.3-0.4 | 9 | 0.333 |
| 0.4-0.5 | 15 | 0.6 |
| 0.5-0.6 | 277 | 0.957 |
| 0.6-0.7 | 19 | 0.684 |
| 0.7-0.8 | 257 | 0.868 |
| 0.8-0.9 | 66 | 0.985 |

## System

- images: 108, mean latency 0.843 s (p50 0.628, p95 0.972), throughput ≈ 71.2 img/min (single process, 12 logical CPUs)
- peak RSS: 183 MB · failure rate: 0.0
- environment: Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.36, Python 3.12.14

## Per-group field detail

| Field | Group | N | Exact |
|---|---|---:|---:|
| address.city | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| address.city | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.6667 |
| address.city | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| address.city | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=en|quality=rotated|type=printed | 3 | 0.6667 |
| address.city | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.3333 |
| address.city | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| address.city | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| address.city | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.6667 |
| address.country | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 0.0 |
| address.country | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| address.country | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.6667 |
| address.country | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 0.3333 |
| address.country | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| address.country | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.3333 |
| address.country | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=low_res|type=printed | 3 | 0.3333 |
| address.country | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| address.country | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=en|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 0.3333 |
| address.country | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=low_res|type=printed | 3 | 0.3333 |
| address.country | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| address.country | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| address.country | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.3333 |
| address.postal_code | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| address.postal_code | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| address.postal_code | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| address.postal_code | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.3333 |
| address.postal_code | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| address.postal_code | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| address.postal_code | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.3333 |
| arabic_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 0.6667 |
| arabic_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 0.6667 |
| arabic_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| arabic_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.3333 |
| arabic_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 0.6667 |
| arabic_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.0 |
| arabic_name | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.6667 |
| arabic_name | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| arabic_name | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| arabic_name | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.0 |
| company | business_card|lang=ar_en|quality=clean|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_en|quality=faded|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_en|quality=photo|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.0 |
| company | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.0 |
| company | business_card|lang=ar|quality=clean|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar|quality=faded|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.6667 |
| company | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| company | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.3333 |
| company | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| company | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| company | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr_en|quality=clean|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr_en|quality=faded|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr_en|quality=photo|type=printed | 3 | 0.6667 |
| company | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr|quality=clean|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr|quality=faded|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr|quality=low_res|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr|quality=photo|type=printed | 3 | 0.3333 |
| company | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.0 |
| first_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| first_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.3333 |
| first_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.0 |
| first_name | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=low_res|type=printed | 3 | 0.6667 |
| first_name | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| first_name | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| first_name | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.3333 |
| first_name | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| first_name | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| first_name | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.0 |
| full_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| full_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.3333 |
| full_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.0 |
| full_name | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.6667 |
| full_name | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| full_name | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.0 |
| full_name | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=low_res|type=printed | 3 | 0.6667 |
| full_name | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| full_name | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| full_name | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.3333 |
| full_name | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| full_name | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| full_name | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.0 |
| industry | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| industry | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.6667 |
| industry | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.6667 |
| industry | business_card|lang=ar|quality=clean|type=printed | 3 | 0.6667 |
| industry | business_card|lang=ar|quality=faded|type=printed | 3 | 0.3333 |
| industry | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.6667 |
| industry | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| industry | business_card|lang=ar|quality=photo|type=printed | 3 | 0.6667 |
| industry | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.6667 |
| industry | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=noisy|type=printed | 3 | 0.6667 |
| industry | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| industry | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.0 |
| industry | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| industry | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| industry | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.3333 |
| job_title | business_card|lang=ar|quality=clean|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar|quality=faded|type=printed | 3 | 0.3333 |
| job_title | business_card|lang=ar|quality=low_res|type=printed | 3 | 0.0 |
| job_title | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| job_title | business_card|lang=ar|quality=photo|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=low_res|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=en|quality=noisy|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| job_title | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.0 |
| job_title | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| job_title | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| job_title | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.6667 |
| last_name | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| last_name | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.3333 |
| last_name | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.0 |
| last_name | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=low_res|type=printed | 3 | 0.6667 |
| last_name | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| last_name | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=en|quality=rotated|type=printed | 3 | 0.3333 |
| last_name | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.3333 |
| last_name | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| last_name | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| last_name | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.0 |
| website | business_card|lang=ar_en|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=low_res|type=printed | 3 | 0.3333 |
| website | business_card|lang=ar_en|quality=noisy|type=printed | 3 | 0.6667 |
| website | business_card|lang=ar_en|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_en|quality=rotated|type=printed | 3 | 0.0 |
| website | business_card|lang=ar_fr|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=low_res|type=printed | 3 | 0.6667 |
| website | business_card|lang=ar_fr|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=ar_fr|quality=rotated|type=printed | 3 | 0.0 |
| website | business_card|lang=ar|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=noisy|type=printed | 3 | 0.0 |
| website | business_card|lang=ar|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=ar|quality=rotated|type=printed | 3 | 0.0 |
| website | business_card|lang=en|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=low_res|type=printed | 3 | 0.3333 |
| website | business_card|lang=en|quality=noisy|type=printed | 3 | 0.3333 |
| website | business_card|lang=en|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=en|quality=rotated|type=printed | 3 | 0.0 |
| website | business_card|lang=fr_en|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=low_res|type=printed | 3 | 0.6667 |
| website | business_card|lang=fr_en|quality=noisy|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=fr_en|quality=rotated|type=printed | 3 | 0.0 |
| website | business_card|lang=fr|quality=clean|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=faded|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=low_res|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=noisy|type=printed | 3 | 0.6667 |
| website | business_card|lang=fr|quality=photo|type=printed | 3 | 1.0 |
| website | business_card|lang=fr|quality=rotated|type=printed | 3 | 0.0 |
