/**
 * TypeScript mirror of packages/shared-types/shared_types/schemas.py and apps/api/app/schemas.py.
 * Keep in sync with the Pydantic models (the API's OpenAPI document is the source of truth).
 */

export type Side = "front" | "back";
export type Lang = "en" | "fr" | "ar";
export type ExtractionMethod = "ocr" | "rule" | "layout" | "ner" | "llm" | "qr" | "manual";
export type ReviewStatus = "unreviewed" | "needs_review" | "verified" | "corrected" | "rejected";
export type DocStatus = "draft" | "ready" | "queued" | "processing" | "completed" | "failed";
export type Product = "business_card";

export interface BBox { x: number; y: number; w: number; h: number }

export interface FieldValue<T = unknown> {
  value: T | null;
  original_value: string | null;
  normalized_value: unknown;
  confidence: number | null;
  source_region_ids: string[];
  extraction_method: ExtractionMethod;
  review_status: ReviewStatus;
  notes: string | null;
}

export interface Address {
  id: string;
  original_text: string;
  normalized_text: string | null;
  street: string | null;
  building: string | null;
  postal_code: string | null;
  city: string | null;
  region: string | null;
  country: string | null;
  role: "business" | "unknown";
  role_confidence: number | null;
  role_evidence: string | null;
  confidence: number | null;
  source_region_ids: string[];
  extraction_method: ExtractionMethod;
  review_status: ReviewStatus;
}

export interface CandidateRegion {
  id: string;
  side: Side;
  label: "address" | "logo" | "text_block" | "qr";
  bbox: BBox;
  confidence: number | null;
  method: string;
  line_ids: string[];
}

export interface QrCode {
  id: string;
  side: Side;
  raw: string;
  kind: "url" | "vcard" | "mecard" | "email" | "tel" | "text" | "wifi";
  parsed: Record<string, string[]>;
  url_is_safe: boolean | null;
  bbox: BBox | null;
  imported: boolean;
}

export interface LanguageRegion { language: string; script: string; line_ids: string[]; share: number }

interface ExtractionBase {
  schema_version: string;
  language_regions: LanguageRegion[];
  languages: string[];
  warnings: string[];
  extractor: string;
  extractor_version: string;
  generated_at: string | null;
}

export interface Phone {
  type: "phone" | "mobile" | "fax" | "whatsapp" | "unknown";
  type_evidence: string | null;
  original: string;
  e164: string | null;
  region: string | null;
  region_inferred_from: "explicit_prefix" | "default_region" | "card_address" | "none";
  is_valid: boolean;
  confidence: number | null;
  source_region_ids: string[];
  review_status: ReviewStatus;
}

export interface BusinessCardData extends ExtractionBase {
  full_name: FieldValue<string>;
  first_name: FieldValue<string>;
  last_name: FieldValue<string>;
  arabic_name: FieldValue<string>;
  job_title: FieldValue<string>;
  company: FieldValue<string>;
  department: FieldValue<string>;
  industry: FieldValue<string>;
  specialty: FieldValue<string>;
  phones: Phone[];
  emails: FieldValue<string>[];
  website: FieldValue<string>;
  linkedin: FieldValue<string>;
  social_profiles: FieldValue<string>[];
  address: Address | null;
  qualifications: FieldValue<string>[];
  certifications: FieldValue<string>[];
  memberships: FieldValue<string>[];
  qr_codes: QrCode[];
  logo: CandidateRegion | null;
  professional_description?: FieldValue<string>;
  qr_checks?: QrFieldCheck[];
  review_fields?: string[];
}

export interface QrFieldCheck {
  field: string;
  qr_id: string;
  qr_value: string;
  ocr_value: string | null;
  status: "match" | "conflict" | "qr_only";
}

export interface ImageInfo {
  side: Side;
  mime: string;
  width: number;
  height: number;
  processed_width: number | null;
  processed_height: number | null;
  size_bytes: number;
  sha256: string;
  url: string;
  processed_url: string | null;
}

export interface Job {
  id: string;
  document_id: string;
  status: "queued" | "running" | "completed" | "failed";
  error_code: string | null;
  error_message: string | null;
  provider: string | null;
  model_metadata: { provider: string; task: string; name: string; version: string | null; languages: string[]; device: string | null }[] | null;
  preprocessing: Record<string, { steps: { name: string; applied: boolean; details: Record<string, unknown> }[]; rotation_applied: number; ocr_ms: number }> | null;
  quality: Record<string, { warnings: string[]; blur_score: number; brightness: number; contrast: number } | null> | null;
  processing_ms: number | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  options: Record<string, unknown> | null;
}

export interface OcrLine {
  id: string;
  side: Side;
  text: string | null;
  normalized_text: string | null;
  bbox: BBox;
  polygon: number[][] | null;
  confidence: number | null;
  script: string | null;
  language: string | null;
  direction: "rtl" | "ltr" | null;
  model: string | null;
  block_index: number | null;
  line_index: number | null;
  extra: Record<string, unknown> | null;
}

export interface Region { id: string; side: Side; label: string | null; bbox: BBox; confidence: number | null; method: string | null; line_ids: string[] }
export interface OcrPage { side: Side; width: number | null; height: number | null; lines: OcrLine[]; regions: Region[] }

export interface DocumentOut<D = BusinessCardData> {
  id: string;
  product: Product;
  client_ref: string | null;
  title: string | null;
  notes: string | null;
  status: DocStatus;
  review_status: ReviewStatus;
  version: number;
  languages: string[] | null;
  data: D | null;
  machine_data: D | null;
  images: ImageInfo[];
  latest_job: Job | null;
  ocr: OcrPage[] | null;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
}

export interface DocumentSummary {
  id: string;
  product: Product;
  title: string | null;
  status: DocStatus;
  review_status: ReviewStatus;
  languages: string[] | null;
  summary: Record<string, string | null>;
  sides: Side[];
  created_at: string;
  updated_at: string;
}

export interface PageOf<T> { items: T[]; total: number; page: number; page_size: number }

export interface FieldChange { path: string; op?: "set" | "append" | "remove" | "verify"; value?: unknown }

export interface ReviewEvent { id: string; action: string; path: string | null; old_value: unknown; new_value: unknown; note: string | null; user_id: string | null; created_at: string }

export interface Duplicate { document: DocumentSummary; matched_keys: string[]; score: number }

export interface Me { id: string; email: string; display_name: string | null; locale: Lang; default_phone_region: string | null; workspace_id: string; workspace_name: string; role: string; android_app_url: string | null }

export interface ApiErrorBody { error: { code: string; message: string; details: Record<string, unknown>; request_id: string | null } }
