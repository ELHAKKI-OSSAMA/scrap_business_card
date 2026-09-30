import { Check, Crosshair, ExternalLink, Plus, QrCode, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { BusinessCardData, FieldChange, FieldValue, Phone, QrCode as Qr } from "@ocr/shared-types";
import { Alert, Badge, Bidi, Button, Card, ConfidenceBadge, FieldRow, ReviewBadge, safeHttpUrl, useErrorMessage, useToast, type WorkspaceRenderProps } from "@ocr/ui";

type Actions = WorkspaceRenderProps<BusinessCardData>["actions"];
const PHONE_TYPES: Phone["type"][] = ["unknown", "phone", "mobile", "fax", "whatsapp"];

function useSafe(actions: Actions) {
  const toast = useToast();
  const errMsg = useErrorMessage();
  return async (changes: FieldChange[]) => {
    try { await actions.patch(changes); return true; } catch (e) { toast("danger", errMsg(e)); return false; }
  };
}

function AddInline({ placeholder, onAdd, dir = "auto", type = "text" }: { placeholder: string; onAdd: (v: string) => Promise<boolean>; dir?: "auto" | "ltr"; type?: string }) {
  const [v, setV] = useState("");
  const { t } = useTranslation();
  return (
    <form className="flex gap-2" onSubmit={async (e) => { e.preventDefault(); if (v.trim() && (await onAdd(v.trim()))) setV(""); }}>
      <input className="input" dir={dir} type={type} placeholder={placeholder} value={v} onChange={(e) => setV(e.target.value)} aria-label={placeholder} />
      <Button type="submit" size="sm" disabled={!v.trim()}><Plus className="size-4" aria-hidden />{t("common.add")}</Button>
    </form>
  );
}

function PhoneRow({ p, i, actions }: { p: Phone; i: number; actions: Actions }) {
  const { t } = useTranslation();
  const apply = useSafe(actions);
  const [e164, setE164] = useState(p.e164 ?? "");
  useEffect(() => setE164(p.e164 ?? ""), [p.e164]);
  return (
    <div className={`flex flex-col gap-2 rounded-lg border p-3 ${p.review_status === "needs_review" ? "border-amber-300 bg-amber-50/60 dark:border-amber-800 dark:bg-amber-950/30" : "border-line"}`}>
      <div className="flex flex-wrap items-center gap-2">
        <select className="input w-auto" aria-label={t("card.fields.phones")} value={p.type} onChange={(e) => apply([{ path: `phones.${i}.type`, value: e.target.value }])}>
          {PHONE_TYPES.map((k) => <option key={k} value={k}>{t(`card.phoneTypes.${k}`)}</option>)}
        </select>
        {p.type_evidence && <Badge title={t("card.phone.labelEvidence")}>“<Bidi>{p.type_evidence}</Bidi>”</Badge>}
        <div className="ms-auto flex items-center gap-1">
          <ConfidenceBadge value={p.confidence} />
          {p.review_status !== "unreviewed" && <ReviewBadge status={p.review_status} />}
          {p.source_region_ids.length > 0 && <Button size="sm" variant="ghost" aria-label={t("viewer.locate")} onClick={() => actions.onLocate(p.source_region_ids)}><Crosshair className="size-4" /></Button>}
          {p.review_status !== "verified" && <Button size="sm" variant="ghost" aria-label={t("review.verifyField")} onClick={() => apply([{ path: `phones.${i}`, op: "verify" }])}><Check className="size-4" /></Button>}
          <Button size="sm" variant="ghost" aria-label={t("common.remove")} onClick={() => apply([{ path: `phones.${i}`, op: "remove" }])}><Trash2 className="size-4" /></Button>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        <div className="text-sm"><span className="block text-xs text-ink-3">{t("card.phone.original")}</span><span dir="ltr" className="ocr-text">{p.original}</span></div>
        <label className="flex flex-col text-xs text-ink-3">{t("card.phone.e164")}
          <input className="input" dir="ltr" value={e164} placeholder={t("card.phone.notNormalized")} onChange={(e) => setE164(e.target.value)}
            onBlur={() => e164 !== (p.e164 ?? "") && apply([{ path: `phones.${i}.e164`, value: e164 || null }])} />
        </label>
      </div>
    </div>
  );
}

function FieldList({ label, name, items, actions }: { label: string; name: "emails" | "qualifications" | "certifications" | "memberships" | "social_profiles"; items: FieldValue<string>[]; actions: Actions }) {
  const { t } = useTranslation();
  const apply = useSafe(actions);
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold">{label} <Badge>{items.length}</Badge></h3>
      {items.map((f, i) => (
        <div key={i} className="relative">
          <FieldRow label={`${label} ${i + 1}`} path={`${name}.${i}`} field={f} actions={actions} dir={name === "emails" ? "ltr" : "auto"} details />
          <Button size="sm" variant="ghost" className="absolute end-2 bottom-2" aria-label={t("common.remove")} onClick={() => apply([{ path: `${name}.${i}`, op: "remove" }])}><Trash2 className="size-4" /></Button>
        </div>
      ))}
      <AddInline placeholder={name === "emails" ? t("fields.addEmail") : `${t("fields.addItem")} — ${label}`} dir={name === "emails" ? "ltr" : "auto"} type={name === "emails" ? "email" : "text"}
        onAdd={(v) => apply([{ path: name, op: "append", value: v }])} />
    </section>
  );
}

function QrPanel({ data, actions }: { data: BusinessCardData; actions: Actions }) {
  const { t } = useTranslation();
  const apply = useSafe(actions);
  if (!data.qr_codes.length) return null;
  const importQr = (q: Qr, i: number) => {
    const ch: FieldChange[] = [];
    const first = (k: string) => q.parsed[k]?.[0];
    if (q.kind === "vcard" || q.kind === "mecard") {
      const fn = first("fn") ?? first("n")?.replace(/;/g, " ").trim();
      if (fn && !data.full_name.value) ch.push({ path: "full_name", value: fn });
      if (first("org") && !data.company.value) ch.push({ path: "company", value: first("org")!.split(";")[0] });
      if (first("title") && !data.job_title.value) ch.push({ path: "job_title", value: first("title") });
      (q.parsed.tel ?? []).forEach((tel) => { if (!data.phones.some((p) => p.original === tel || p.e164 === tel)) ch.push({ path: "phones", op: "append", value: { original: tel } }); });
      (q.parsed.email ?? []).forEach((em) => { if (!data.emails.some((e) => e.value === em)) ch.push({ path: "emails", op: "append", value: em }); });
      const url = first("url");
      if (url && safeHttpUrl(url) && !data.website.value) ch.push({ path: "website", value: url });
    } else if (q.kind === "url" && q.url_is_safe && !data.website.value) {
      ch.push({ path: "website", value: q.raw });
    } else if (q.kind === "email") {
      ch.push({ path: "emails", op: "append", value: q.parsed.email?.[0] });
    } else if (q.kind === "tel") {
      ch.push({ path: "phones", op: "append", value: { original: q.parsed.tel?.[0] } });
    }
    ch.push({ path: `qr_codes.${i}.imported`, value: true });
    return apply(ch);
  };
  return (
    <Card className="flex flex-col gap-3 p-4">
      <h3 className="flex items-center gap-2 font-semibold"><QrCode className="size-4" aria-hidden />{t("card.qr")}</h3>
      <Alert tone="info">{t("card.qrNote")}</Alert>
      <QrComparison data={data} />
      {data.qr_codes.map((q, i) => {
        const safe = q.kind === "url" && q.url_is_safe ? safeHttpUrl(q.raw) : null;
        return (
          <div key={q.id} className="flex flex-col gap-2 rounded-lg border border-line p-3">
            <div className="flex items-center gap-2"><Badge>{q.kind}</Badge>{q.imported && <Badge tone="success">{t("card.qrImported")}</Badge>}</div>
            <p className="text-xs text-ink-3">{t("card.qrRaw")}</p>
            {/* raw content is shown as inert text, never interpreted */}
            <pre dir="ltr" className="max-h-40 overflow-auto whitespace-pre-wrap break-all rounded bg-surface-2 p-2 text-xs">{q.raw}</pre>
            {q.kind === "url" && (safe
              ? <a href={safe} target="_blank" rel="noopener noreferrer nofollow" className="inline-flex items-center gap-1 text-sm text-accent-ink underline" dir="ltr">{safe}<ExternalLink className="size-3" aria-hidden /></a>
              : <p className="text-xs text-amber-700 dark:text-amber-300">{t("card.qrUnsafe")}</p>)}
            {!q.imported && <div><Button size="sm" onClick={() => importQr(q, i)}>{t("card.qrImport")}</Button></div>}
          </div>
        );
      })}
    </Card>
  );
}

function QrComparison({ data }: { data: BusinessCardData }) {
  const { t } = useTranslation();
  const checks = data.qr_checks ?? [];
  if (!checks.length) return null;
  const tone = (s: string): "success" | "danger" | "warning" => (s === "match" ? "success" : s === "conflict" ? "danger" : "warning");
  return (
    <div className="flex flex-col gap-2" data-testid="qr-comparison">
      <h4 className="text-sm font-semibold">{t("card.qrCompare")}</h4>
      {checks.some((c) => c.status !== "match") && <Alert tone="warning">{t("card.qrConflictNote")}</Alert>}
      <div className="overflow-x-auto">
        <table className="w-full text-start text-sm">
          <thead><tr className="text-xs text-ink-3"><th className="p-1 text-start">{t("card.qrField")}</th><th className="p-1 text-start">{t("card.qrValue")}</th><th className="p-1 text-start">{t("card.qrOcr")}</th><th className="p-1" /></tr></thead>
          <tbody>
            {checks.map((c, i) => (
              <tr key={i} className="border-t border-line">
                <td className="p-1">{t(`card.fields.${c.field}`)}</td>
                <td className="p-1 ocr-text"><Bidi>{c.qr_value}</Bidi></td>
                <td className="p-1 ocr-text">{c.ocr_value ? <Bidi>{c.ocr_value}</Bidi> : <span className="italic text-ink-3">—</span>}</td>
                <td className="p-1"><Badge tone={tone(c.status)}>{t(`card.qrStatus.${c.status}`)}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AddressEditor({ data, actions }: { data: BusinessCardData; actions: Actions }) {
  const { t } = useTranslation();
  const apply = useSafe(actions);
  const a = data.address;
  if (!a) {
    return (
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">{t("card.fields.address")}</h3>
        <AddInline placeholder={t("card.fields.address")} onAdd={(v) => apply([{ path: "address", value: { id: "addr-m", original_text: v, role: "business", extraction_method: "manual", review_status: "corrected" } }])} />
      </section>
    );
  }
  const parts = ["street", "building", "postal_code", "city", "region", "country"] as const;
  return (
    <section className="flex flex-col gap-2 rounded-lg border border-line p-3">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold">{t("card.fields.address")}</h3>
        <div className="ms-auto flex items-center gap-1">
          <ConfidenceBadge value={a.confidence} />
          {a.review_status !== "unreviewed" && <ReviewBadge status={a.review_status} />}
          <Button size="sm" variant="ghost" aria-label={t("viewer.locate")} onClick={() => actions.onLocate(a.source_region_ids)}><Crosshair className="size-4" /></Button>
        </div>
      </div>
      <Bidi as="p" className="ocr-text whitespace-pre-wrap rounded-md bg-surface-2 p-2 text-sm">{a.original_text}</Bidi>
      <div className="grid grid-cols-2 gap-2">
        {parts.map((k) => (
          <label key={k} className="flex flex-col gap-0.5 text-xs text-ink-2">{t(`card.fields.${k}`)}
            <input className="input ocr-text" dir="auto" defaultValue={a[k] ?? ""} key={`${k}-${a[k]}`} onBlur={(e) => e.target.value !== (a[k] ?? "") && apply([{ path: `address.${k}`, value: e.target.value || null }])} />
          </label>
        ))}
      </div>
    </section>
  );
}

export function CardFields({ data, actions }: WorkspaceRenderProps<BusinessCardData>) {
  const { t } = useTranslation();
  const f = (k: string) => t(`card.fields.${k}`);
  const apply = useSafe(actions);
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <FieldRow label={f("full_name")} path="full_name" field={data.full_name} actions={actions} details />
        <FieldRow label={f("arabic_name")} path="arabic_name" field={data.arabic_name} actions={actions} dir="rtl" details />
        <FieldRow label={f("first_name")} path="first_name" field={data.first_name} actions={actions} details />
        <FieldRow label={f("last_name")} path="last_name" field={data.last_name} actions={actions} details />
        <FieldRow label={f("job_title")} path="job_title" field={data.job_title} actions={actions} details />
        <FieldRow label={f("company")} path="company" field={data.company} actions={actions} details />
        <FieldRow label={f("department")} path="department" field={data.department} actions={actions} details />
        <FieldRow label={f("industry")} path="industry" field={data.industry} actions={actions} details />
        <FieldRow label={f("specialty")} path="specialty" field={data.specialty} actions={actions} details />
      </div>
      <FieldRow label={f("professional_description")} path="professional_description" field={data.professional_description} actions={actions} multiline details />
      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold">{f("phones")} <Badge>{data.phones.length}</Badge></h3>
        {data.phones.map((p, i) => <PhoneRow key={`${i}-${p.original}`} p={p} i={i} actions={actions} />)}
        <AddInline placeholder={t("fields.addPhone")} dir="ltr" type="tel" onAdd={(v) => apply([{ path: "phones", op: "append", value: { original: v } }])} />
      </section>
      <FieldList label={f("emails")} name="emails" items={data.emails} actions={actions} />
      <div className="grid gap-3 sm:grid-cols-2">
        <FieldRow label={f("website")} path="website" field={data.website} actions={actions} dir="ltr" details />
        <FieldRow label={f("linkedin")} path="linkedin" field={data.linkedin} actions={actions} dir="ltr" details />
      </div>
      <FieldList label={f("social_profiles")} name="social_profiles" items={data.social_profiles} actions={actions} />
      <AddressEditor data={data} actions={actions} />
      <FieldList label={f("qualifications")} name="qualifications" items={data.qualifications} actions={actions} />
      <FieldList label={f("certifications")} name="certifications" items={data.certifications} actions={actions} />
      <FieldList label={f("memberships")} name="memberships" items={data.memberships} actions={actions} />
      <QrPanel data={data} actions={actions} />
      {data.logo && <p className="text-xs text-ink-3">{t("card.logo")}: {Math.round((data.logo.confidence ?? 0) * 100)}% · {t("viewer.candidate")}</p>}
    </div>
  );
}
