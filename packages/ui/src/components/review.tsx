import { Check, Crosshair, Download, Languages, Pencil, X } from "lucide-react";
import { useEffect, useId, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { FieldValue, Job, OcrPage, ReviewEvent } from "@ocr/shared-types";
import { accountApi } from "../lib/api";
import { translateNote } from "../lib/notes";
import { formatDateTime, formatNumber, formatPercent } from "../lib/format";
import { useErrorMessage, useJob } from "../lib/hooks";
import { Alert, Badge, Bidi, Button, ConfidenceBadge, MethodChip, ReviewBadge, Spinner, cx } from "./primitives";

export interface FieldActions {
  onSet: (path: string, value: unknown) => Promise<void>;
  onVerify: (path: string) => Promise<void>;
  onLocate: (ids: string[]) => void;
}

/** One extracted field: value (editable), OCR evidence, confidence, method and review state. */
export function FieldRow({ label, path, field, actions, multiline, dir, readOnly, hint, details }: {
  label: string; path: string; field: FieldValue<unknown> | undefined; actions: FieldActions; multiline?: boolean; dir?: "ltr" | "rtl" | "auto"; readOnly?: boolean; hint?: ReactNode;
  /** opt-in: also show the normalized value and source OCR region ids (off by default) */
  details?: boolean;
}) {
  const { t } = useTranslation();
  const id = useId();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const errMsg = useErrorMessage();
  const value = field?.value == null ? "" : String(field.value);
  useEffect(() => { if (!editing) setDraft(value); }, [value, editing]);
  const uncertain = field?.review_status === "needs_review";
  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await actions.onSet(path, draft.trim() === "" ? null : draft);
      setEditing(false);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  };
  const Input = multiline ? "textarea" : "input";
  return (
    <div className={cx("rounded-lg border p-3", uncertain ? "border-amber-300 bg-amber-50/60 dark:border-amber-800 dark:bg-amber-950/30" : "border-line bg-surface")} data-field={path}>
      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor={id} className="text-xs font-semibold uppercase tracking-wide text-ink-2">{label}</label>
        <div className="ms-auto flex flex-wrap items-center gap-1">
          {field && field.value != null && <ConfidenceBadge value={field.confidence} />}
          {field && field.value != null && <MethodChip method={field.extraction_method} />}
          {field && field.review_status !== "unreviewed" && <ReviewBadge status={field.review_status} />}
        </div>
      </div>
      {editing ? (
        <div className="mt-2 flex flex-col gap-2">
          <Input id={id} dir={dir ?? "auto"} className="input ocr-text" rows={multiline ? 5 : undefined} value={draft} onChange={(e: React.ChangeEvent<HTMLInputElement & HTMLTextAreaElement>) => setDraft(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent) => { if (!multiline && e.key === "Enter") save(); if (e.key === "Escape") setEditing(false); }} autoFocus />
          {error && <Alert tone="danger">{error}</Alert>}
          <div className="flex gap-2">
            <Button size="sm" variant="primary" onClick={save} loading={busy}><Check className="size-4" aria-hidden />{t("common.save")}</Button>
            <Button size="sm" onClick={() => { setEditing(false); setError(null); }}><X className="size-4" aria-hidden />{t("common.cancel")}</Button>
          </div>
        </div>
      ) : (
        <div className="mt-1 flex items-start gap-2">
          <p id={id} className={cx("min-w-0 flex-1 break-words text-[15px] ocr-text", multiline && "whitespace-pre-wrap", field?.value == null && "italic text-ink-3")} dir={dir ?? "auto"}>
            {field?.value == null ? t("fields.noValue") : value}
          </p>
          <div className="flex shrink-0 gap-0.5">
            {field && field.source_region_ids.length > 0 && (
              <Button size="sm" variant="ghost" aria-label={t("viewer.locate")} title={t("viewer.locate")} onClick={() => actions.onLocate(field.source_region_ids)}><Crosshair className="size-4" /></Button>
            )}
            {!readOnly && field?.value != null && field.review_status !== "verified" && (
              <Button size="sm" variant="ghost" aria-label={t("review.verifyField")} title={t("review.verifyField")} onClick={() => actions.onVerify(path)}><Check className="size-4" /></Button>
            )}
            {!readOnly && <Button size="sm" variant="ghost" aria-label={`${t("common.edit")} ${label}`} onClick={() => setEditing(true)}><Pencil className="size-4" /></Button>}
          </div>
        </div>
      )}
      {field?.original_value && field.original_value !== value && (
        <p className="mt-1 text-xs text-ink-3"><span className="font-medium">{t("fields.evidence")}:</span> <Bidi className="ocr-text">{field.original_value}</Bidi></p>
      )}
      {details && field?.value != null && field.normalized_value != null && String(field.normalized_value) !== value && (
        <p className="mt-0.5 text-xs text-ink-3"><span className="font-medium">{t("fields.normalized")}:</span> <Bidi className="ocr-text">{String(field.normalized_value)}</Bidi></p>
      )}
      {details && field && field.source_region_ids.length > 0 && (
        <p className="mt-0.5 text-xs text-ink-3" dir="ltr"><span className="font-medium">{t("fields.source")}:</span> {field.source_region_ids.join(", ")}</p>
      )}
      {field?.notes && <p className="mt-0.5 text-xs text-ink-3">{translateNote(field.notes, t)}</p>}
      {hint}
    </div>
  );
}

export function OcrTextPanel({ pages, selected, onSelect }: { pages: OcrPage[]; selected: string[]; onSelect: (id: string) => void }) {
  const { t, i18n } = useTranslation();
  const [translation, setTranslation] = useState<Record<string, string>>({});
  const [trError, setTrError] = useState<string | null>(null);
  const lines = pages.flatMap((p) => p.lines.map((l) => ({ ...l, side: p.side })));
  const translate = async (id: string, text: string) => {
    try {
      const r = await accountApi.translate(text, i18n.language);
      setTranslation((m) => ({ ...m, [id]: r.translated_text }));
    } catch {
      setTrError(t("ocr.translationUnavailable"));
    }
  };
  if (!lines.length) return <p className="text-sm text-ink-3">{t("ocr.empty")}</p>;
  return (
    <div className="flex flex-col gap-2">
      <Alert tone="info">{t("ocr.notice")}</Alert>
      {trError && <Alert tone="warning">{trError}</Alert>}
      <ol className="flex flex-col gap-1.5">
        {lines.map((l) => (
          <li key={l.id}>
            <button onClick={() => onSelect(l.id)} aria-pressed={selected.includes(l.id)} className={cx("w-full rounded-lg border px-3 py-2 text-start", selected.includes(l.id) ? "border-amber-400 bg-amber-50 dark:bg-amber-950/40" : "border-line bg-surface hover:bg-surface-2")}>
              <p dir={l.direction ?? "auto"} lang={l.language && l.language !== "und" ? l.language : undefined} className="ocr-text text-[15px] text-ink">{l.text || <span className="italic text-ink-3">∅</span>}</p>
              <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-ink-3">
                <Badge>{t(`upload.${l.side}`)}</Badge>
                <Badge>{t(`lang.${l.language ?? "und"}`, { defaultValue: l.language ?? "und" })} · {l.script}</Badge>
                <Badge title={t("confidence.disclaimer")}>{t("confidence.label")} {formatPercent(l.confidence, i18n.language)}</Badge>
                <span dir="ltr" className="font-mono">{l.model}</span>
                {l.normalized_text && l.normalized_text !== l.text && <span>· {t("ocr.normalized")}: <Bidi>{l.normalized_text}</Bidi></span>}
              </div>
            </button>
            {translation[l.id] ? (
              <p className="mt-1 rounded-md bg-surface-2 px-3 py-1.5 text-sm text-ink-2"><Badge tone="warning">{t("ocr.translationNote")}</Badge> <Bidi>{translation[l.id]}</Bidi></p>
            ) : (
              l.text && l.language && l.language !== i18n.language && l.language !== "und" && (
                <button className="mt-0.5 inline-flex items-center gap-1 text-xs text-accent-ink underline" onClick={() => translate(l.id, l.text!)}><Languages className="size-3" />{t("ocr.translate")}</button>
              )
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function HistoryPanel({ events }: { events: ReviewEvent[] | undefined }) {
  const { t, i18n } = useTranslation();
  if (!events) return <Spinner />;
  if (!events.length) return <p className="text-sm text-ink-3">{t("history.empty")}</p>;
  const show = (v: unknown) => {
    if (v == null) return "—";
    if (typeof v === "object" && v && "value" in (v as Record<string, unknown>)) return String((v as Record<string, unknown>).value ?? "—");
    return typeof v === "string" ? v : JSON.stringify(v);
  };
  return (
    <ol className="flex flex-col gap-2">
      {events.map((e) => (
        <li key={e.id} className="rounded-lg border border-line bg-surface p-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="font-medium">{t(`history.${e.action}`, { path: e.path ?? "" })}</span>
            <time className="text-xs text-ink-3" dateTime={e.created_at}>{formatDateTime(e.created_at, i18n.language)}</time>
          </div>
          {(e.action === "field_set" || e.action === "review") && (
            <p className="mt-1 text-xs text-ink-2"><del className="text-ink-3"><Bidi>{show(e.old_value)}</Bidi></del> → <Bidi>{show(e.new_value)}</Bidi></p>
          )}
          {e.note && <p className="mt-1 text-xs text-ink-3">{e.note}</p>}
        </li>
      ))}
    </ol>
  );
}

export const LANG_OPTIONS = ["ar", "fr", "en"] as const;

export function ProcessPanel({ hasImages, status, jobId, onRun, busy, processed, onDone }: {
  hasImages: boolean; status: string; jobId: string | null; onRun: (langs: string[] | null, force: boolean) => void; busy?: boolean; processed: boolean; onDone?: (j: Job) => void;
}) {
  const { t } = useTranslation();
  const [langs, setLangs] = useState<string[]>([...LANG_OPTIONS]);
  const job = useJob(jobId, onDone);
  const running = status === "queued" || status === "processing" || job.data?.status === "queued" || job.data?.status === "running";
  const failed = job.data?.status === "failed" || status === "failed";
  const errMsg = t(`errors.${job.data?.error_code ?? "processing_error"}`, { defaultValue: t("errors.processing_error") });
  return (
    <div className="flex flex-col gap-3">
      <fieldset className="flex flex-col gap-1.5">
        <legend className="text-sm font-medium text-ink">{t("process.languages")}</legend>
        <div className="flex flex-wrap gap-3">
          {LANG_OPTIONS.map((l) => (
            <label key={l} className="inline-flex items-center gap-1.5 text-sm">
              <input type="checkbox" checked={langs.includes(l)} onChange={(e) => setLangs((xs) => (e.target.checked ? [...xs, l] : xs.filter((x) => x !== l)))} disabled={running} />
              {t(`lang.${l}`)}
            </label>
          ))}
        </div>
        <p className="text-xs text-ink-3">{t("process.languagesHint")}</p>
      </fieldset>
      {processed && <p className="text-xs text-ink-3">{t("process.rerunWarning")}</p>}
      <Button variant="primary" disabled={!hasImages || running || langs.length === 0} loading={busy || running} onClick={() => onRun(langs.length === LANG_OPTIONS.length ? null : langs, processed)}>
        {running ? (job.data?.status === "queued" || status === "queued" ? t("process.queued") : t("process.running")) : processed ? t("process.rerun") : t("process.run")}
      </Button>
      {!hasImages && <p className="text-xs text-ink-3">{t("upload.required")}</p>}
      {failed && <Alert tone="danger" title={t("process.failed")}>{errMsg}{job.data?.error_message && <span className="mt-1 block font-mono text-xs opacity-75" dir="ltr">{job.data.error_message}</span>}</Alert>}
    </div>
  );
}

export function JobDetails({ job }: { job: Job | null }) {
  const { t, i18n } = useTranslation();
  if (!job) return <p className="text-sm text-ink-3">—</p>;
  return (
    <div className="flex flex-col gap-3 text-sm">
      <div className="grid grid-cols-2 gap-2">
        <span className="text-ink-2">{t("status.completed")}</span><span>{formatDateTime(job.finished_at, i18n.language)}</span>
        <span className="text-ink-2">ms</span><span dir="ltr">{formatNumber(job.processing_ms, i18n.language)}</span>
        <span className="text-ink-2">Provider</span><span dir="ltr">{job.provider}</span>
      </div>
      <div>
        <p className="mb-1 font-medium">{t("ocr.model")}</p>
        <ul className="flex flex-col gap-1" dir="ltr">
          {(job.model_metadata ?? []).map((m, i) => (
            <li key={i} className="font-mono text-xs text-ink-2">{m.task}: {m.name} {m.version ? `(${m.provider} ${m.version})` : ""} {m.device ? `· ${m.device}` : ""}</li>
          ))}
        </ul>
      </div>
      {job.preprocessing && Object.entries(job.preprocessing).map(([side, info]) => (
        <div key={side}>
          <p className="mb-1 font-medium">{t(`upload.${side}`)}</p>
          <div className="flex flex-wrap gap-1">
            {info.steps.map((s) => <Badge key={s.name} tone={s.applied ? "accent" : "neutral"}>{s.name}{s.applied ? " ✓" : ""}</Badge>)}
          </div>
          {job.quality?.[side]?.warnings?.length ? <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">{job.quality[side]!.warnings.map((w) => t(`warnings.${w}`, { defaultValue: w })).join(" · ")}</p> : null}
        </div>
      ))}
    </div>
  );
}

export function ExportMenu({ formats, onExport }: { formats: readonly ("json" | "csv" | "vcf")[]; onExport: (f: "json" | "csv" | "vcf") => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label={t("export.title")}>
      {formats.map((f) => <Button key={f} size="sm" onClick={() => onExport(f)}><Download className="size-4" aria-hidden />{t(`export.${f}`)}</Button>)}
    </div>
  );
}

export function WarningList({ warnings }: { warnings: string[] }) {
  const { t } = useTranslation();
  const known = warnings.filter((w) => !w.includes(":") || w.split(":")[1]);
  if (!known.length) return null;
  const label = (w: string) => {
    const [a, b] = w.split(":");
    if (b && (a === "front" || a === "back")) return `${t(`upload.${a}`)}: ${t(`warnings.${b}`, { defaultValue: b })}`;
    return t(`warnings.${a}`, { defaultValue: w });
  };
  return (
    <Alert tone="warning">
      <ul className="list-inside list-disc">{Array.from(new Set(known.map(label))).map((w) => <li key={w}>{w}</li>)}</ul>
    </Alert>
  );
}

