import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FileSearch, Plus, Star, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import type { DocumentOut, DocumentSummary, FieldChange, Side } from "@ocr/shared-types";
import { accountApi, captureApi, productApi, type ProductRoute } from "../lib/api";
import { formatDate, formatDateTime, formatNumber, uuid } from "../lib/format";
import { useDocument, useErrorMessage } from "../lib/hooks";
import { Alert, Bidi, Button, Card, ConfirmDialog, EmptyState, ReviewBadge, Spinner, StatusBadge, cx, useToast } from "./primitives";
import { AndroidIcon, LanguageSelector as LanguageSelectorProxy, ThemeToggle as ThemeToggleProxy } from "./shell";
import { ExportMenu, HistoryPanel, JobDetails, OcrTextPanel, ProcessPanel, WarningList, type FieldActions } from "./review";
import { UploadSlot } from "./upload";
import { ImageViewer } from "./viewer";

export interface ListColumn { key: string; label: string; render: (d: DocumentSummary) => ReactNode }

export interface ProductUi {
  route: ProductRoute;
  i18nKey: "card";
  sides: { side: Side; optional: boolean }[];
  exportFormats: readonly ("json" | "csv" | "vcf")[];
  columns: ListColumn[];
  primaryText: (d: DocumentSummary) => ReactNode;
  /** Heading for the detail page, derived from the extracted data. */
  docTitle: (doc: DocumentOut) => string | null;
  regionLabel?: (label: string) => string;
}

// ---------------------------------------------------------------- list / history
export function DocumentListPage({ ui }: { ui: ProductUi }) {
  const { t, i18n } = useTranslation();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const [text, setText] = useState(q);
  const page = Number(params.get("page") ?? 1);
  const favOnly = params.get("fav") === "1";
  const filters = { q, status: params.get("status") ?? "", review_status: params.get("review_status") ?? "", language: params.get("language") ?? "", favorite: favOnly ? "true" : "", sort: params.get("sort") ?? "updated_desc", page, page_size: 20 };
  const api = productApi(ui.route);
  const qc = useQueryClient();
  const toast = useToast();
  const errMsg = useErrorMessage();
  const list = useQuery({ queryKey: [ui.route, "list", filters], queryFn: () => api.list(filters), placeholderData: (p) => p });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const pageIds = list.data?.items.map((d) => d.id) ?? [];
  const allOnPage = pageIds.length > 0 && pageIds.every((id) => selected.has(id));
  const toggle = (id: string) => setSelected((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const toggleAll = () => setSelected((s) => { const n = new Set(s); pageIds.forEach((id) => (allOnPage ? n.delete(id) : n.add(id))); return n; });
  const refresh = () => qc.invalidateQueries({ queryKey: [ui.route] });
  const setFavorite = async (ids: string[], favorite: boolean) => {
    try {
      await Promise.all(ids.map((id) => api.updateMeta(id, { favorite })));
      await refresh();
    } catch (e) { toast("danger", errMsg(e)); }
  };
  const bulkDelete = async () => {
    setBusy(true);
    try {
      const r = await api.bulkDelete([...selected]);
      toast("success", t("list.deletedCount", { count: r.deleted }));
      setSelected(new Set());
      setConfirmDelete(false);
      await refresh();
    } catch (e) { toast("danger", errMsg(e)); } finally { setBusy(false); }
  };
  useEffect(() => {
    const h = setTimeout(() => { if (text !== q) update({ q: text, page: "" }); }, 350);
    return () => clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);
  const update = (kv: Record<string, string>) => {
    const next = new URLSearchParams(params);
    Object.entries(kv).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setParams(next, { replace: true });
  };
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{t("nav.history")}</h1>
        <div className="flex gap-2">
          <Button variant={favOnly ? "primary" : "secondary"} aria-pressed={favOnly} onClick={() => update({ fav: favOnly ? "" : "1", page: "" })}>
            <Star className={cx("size-4", favOnly && "fill-current")} aria-hidden />{t("list.favorites")}
          </Button>
          <ExportMenu formats={ui.exportFormats} onExport={(f) => api.download(`/${ui.route}/export?format=${f}${q ? `&q=${encodeURIComponent(q)}` : ""}${favOnly ? "&favorite=true" : ""}`, `${ui.route}.${f}`)} />
          <Link to="/new"><Button variant="primary"><Plus className="size-4" aria-hidden />{t(`${ui.i18nKey}.new`)}</Button></Link>
        </div>
      </div>
      <Card className="flex flex-wrap items-end gap-3 p-3">
        <label className="flex min-w-60 flex-1 flex-col gap-1 text-xs text-ink-2">{t("common.search")}
          <input type="search" dir="auto" className="input" placeholder={t("list.searchPlaceholder")} value={text} onChange={(e) => setText(e.target.value)} />
        </label>
        <Select label={t("common.filters")} value={filters.status} onChange={(v) => update({ status: v, page: "" })} options={[["", t("list.anyStatus")], ...["draft", "ready", "processing", "completed", "failed"].map((s) => [s, t(`status.${s}`)] as [string, string])]} />
        <Select label={t("review.status")} value={filters.review_status} onChange={(v) => update({ review_status: v, page: "" })} options={[["", t("list.anyReview")], ...["unreviewed", "needs_review", "verified", "rejected"].map((s) => [s, t(`review.${s}`)] as [string, string])]} />
        <Select label={t("common.language")} value={filters.language} onChange={(v) => update({ language: v, page: "" })} options={[["", t("list.anyLanguage")], ["ar", t("lang.ar")], ["fr", t("lang.fr")], ["en", t("lang.en")]]} />
        <Select label={t("common.filters")} value={filters.sort} onChange={(v) => update({ sort: v })} options={[["updated_desc", t("list.sortUpdated")], ["created_desc", t("list.sortCreated")]]} />
      </Card>
      {list.isError ? (
        <Alert tone="danger" action={<Button size="sm" onClick={() => list.refetch()}>{t("common.retry")}</Button>}>{t("errors.generic")}</Alert>
      ) : list.isLoading ? (
        <Spinner />
      ) : !list.data?.items.length ? (
        <EmptyState icon={<FileSearch className="size-10" />} title={q ? t("empty.search") : t("empty.title")} body={q ? undefined : t(`${ui.i18nKey}.empty`)}
          action={!q && <Link to="/new"><Button variant="primary">{t("empty.cta")}</Button></Link>} />
      ) : (
        <>
          {selected.size > 0 ? (
            <div role="toolbar" aria-label={t("list.selection")} className="sticky top-16 z-20 flex flex-wrap items-center gap-2 rounded-xl border border-accent bg-accent-soft px-3 py-2">
              <span className="text-sm font-medium text-accent-ink">{t("list.selectedCount", { count: selected.size })}</span>
              <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}><X className="size-4" aria-hidden />{t("list.clearSelection")}</Button>
              <span className="ms-auto" />
              <Button size="sm" onClick={() => setFavorite([...selected], true)}><Star className="size-4" aria-hidden />{t("list.addFavorite")}</Button>
              <Button size="sm" onClick={() => setFavorite([...selected], false)}>{t("list.removeFavorite")}</Button>
              <ExportMenu formats={ui.exportFormats} onExport={(f) => api.download(`/${ui.route}/export?format=${f}&ids=${[...selected].join(",")}`, `${ui.route}-selection.${f}`)} />
              <Button size="sm" variant="danger" onClick={() => setConfirmDelete(true)}><Trash2 className="size-4" aria-hidden />{t("common.delete")}</Button>
            </div>
          ) : (
            <p className="text-sm text-ink-2">{t("common.results", { count: list.data.total })}</p>
          )}
          <ConfirmDialog open={confirmDelete} danger busy={busy} title={t("list.deleteSelectedTitle", { count: selected.size })} body={t("list.deleteSelectedBody")}
            confirmLabel={t("common.delete")} onConfirm={bulkDelete} onCancel={() => setConfirmDelete(false)} />
          <div className="overflow-x-auto rounded-xl border border-line bg-surface">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-start text-xs uppercase text-ink-2">
                <tr>
                  <th className="w-10 px-3 py-2"><input type="checkbox" className="size-4" checked={allOnPage} onChange={toggleAll} aria-label={t("list.selectAll")} /></th>
                  <th className="w-10 px-1 py-2"><span className="sr-only">{t("list.favorites")}</span></th>
                  <th className="px-3 py-2 text-start font-medium">{t("common.details")}</th>
                  {ui.columns.map((c) => <th key={c.key} className="px-3 py-2 text-start font-medium">{c.label}</th>)}
                  <th className="px-3 py-2 text-start font-medium">{t("review.status")}</th>
                  <th className="px-3 py-2 text-start font-medium">{t("list.updated")}</th>
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((d) => (
                  <tr key={d.id} className={cx("border-t border-line hover:bg-surface-2", selected.has(d.id) && "bg-accent-soft/50")}>
                    <td className="px-3 py-2"><input type="checkbox" className="size-4" checked={selected.has(d.id)} onChange={() => toggle(d.id)} aria-label={t("list.selectOne", { name: d.title ?? d.id })} /></td>
                    <td className="px-1 py-2">
                      <button onClick={() => setFavorite([d.id], !d.favorite)} aria-pressed={!!d.favorite} title={d.favorite ? t("list.removeFavorite") : t("list.addFavorite")}
                        className={cx("rounded p-1", d.favorite ? "text-amber-500" : "text-ink-3 hover:text-amber-500")}>
                        <Star className={cx("size-4", d.favorite && "fill-current")} aria-hidden />
                      </button>
                    </td>
                    <td className="px-3 py-2"><Link to={`/documents/${d.id}`} className="font-medium text-accent-ink underline-offset-2 hover:underline">{ui.primaryText(d)}</Link><div className="mt-0.5"><StatusBadge status={d.status} /></div></td>
                    {ui.columns.map((c) => <td key={c.key} className="px-3 py-2">{c.render(d)}</td>)}
                    <td className="px-3 py-2"><ReviewBadge status={d.review_status} /></td>
                    <td className="whitespace-nowrap px-3 py-2 text-ink-2">{formatDate(d.updated_at, i18n.language)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <nav className="flex items-center justify-center gap-2" aria-label="pagination">
            <Button size="sm" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>{t("common.prev")}</Button>
            <span className="text-sm text-ink-2">{t("common.page", { page: formatNumber(page, i18n.language), pages: formatNumber(pages, i18n.language) })}</span>
            <Button size="sm" disabled={page >= pages} onClick={() => update({ page: String(page + 1) })}>{t("common.next")}</Button>
          </nav>
        </>
      )}
    </div>
  );
}

function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: [string, string][] }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-2">{label}
      <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>{options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
    </label>
  );
}

// ---------------------------------------------------------------- dashboard
export function DashboardPage({ ui, hero }: { ui: ProductUi; hero?: ReactNode }) {
  const { t, i18n } = useTranslation();
  const api = productApi(ui.route);
  const all = useQuery({ queryKey: [ui.route, "list", "dash-all"], queryFn: () => api.list({ page_size: 6 }) });
  const review = useQuery({ queryKey: [ui.route, "list", "dash-review"], queryFn: () => api.list({ review_status: "needs_review", page_size: 1 }) });
  const done = useQuery({ queryKey: [ui.route, "list", "dash-done"], queryFn: () => api.list({ status: "completed", page_size: 1 }) });
  const failed = useQuery({ queryKey: [ui.route, "list", "dash-failed"], queryFn: () => api.list({ status: "failed", page_size: 1 }) });
  const stats = [
    { label: t("dashboard.total"), v: all.data?.total, to: "/history" },
    { label: t("dashboard.needsReview"), v: review.data?.total, to: "/history?review_status=needs_review" },
    { label: t("dashboard.completed"), v: done.data?.total, to: "/history?status=completed" },
    { label: t("dashboard.failed"), v: failed.data?.total, to: "/history?status=failed" },
  ];
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{t(`app.${ui.i18nKey}.name`)}</h1>
          <p className="text-sm text-ink-2">{t(`app.${ui.i18nKey}.tagline`)}</p>
        </div>
        <Link to="/new"><Button variant="primary"><Plus className="size-4" aria-hidden />{t(`${ui.i18nKey}.new`)}</Button></Link>
      </div>
      {hero}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {stats.map((s) => (
          <Link key={s.label} to={s.to}>
            <Card className="p-4 transition-colors hover:border-accent">
              <p className="text-xs uppercase tracking-wide text-ink-2">{s.label}</p>
              <p className="mt-1 text-3xl font-semibold">{s.v === undefined ? "…" : formatNumber(s.v, i18n.language)}</p>
            </Card>
          </Link>
        ))}
      </div>
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t("dashboard.recent")}</h2>
          <Link to="/history" className="text-sm text-accent-ink underline">{t("dashboard.viewAll")}</Link>
        </div>
        {all.isLoading ? <Spinner /> : !all.data?.items.length ? (
          <Onboarding ui={ui} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {all.data.items.map((d) => (
              <Link key={d.id} to={`/documents/${d.id}`}>
                <Card className="flex h-full flex-col gap-2 p-4 transition-colors hover:border-accent">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium">{ui.primaryText(d)}</p>
                    <StatusBadge status={d.status} />
                  </div>
                  <div className="flex flex-wrap gap-2 text-sm text-ink-2">{ui.columns.slice(0, 2).map((c) => <span key={c.key}>{c.render(d)}</span>)}</div>
                  <div className="mt-auto flex items-center justify-between text-xs text-ink-3"><ReviewBadge status={d.review_status} /><span>{formatDateTime(d.updated_at, i18n.language)}</span></div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Onboarding({ ui }: { ui: ProductUi }) {
  const { t } = useTranslation();
  return (
    <Card className="p-6">
      <ol className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((n) => (
          <li key={n} className="flex gap-3">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-accent-soft font-semibold text-accent-ink">{n}</span>
            <div><p className="font-medium">{t(`onboarding.step${n}`)}</p><p className="text-sm text-ink-2">{t(`onboarding.step${n}Text`)}</p></div>
          </li>
        ))}
      </ol>
      <div className="mt-5 text-center"><Link to="/new"><Button variant="primary">{t("empty.cta")}</Button></Link></div>
      <p className="mt-3 text-center text-xs text-ink-3">{t(`${ui.i18nKey}.empty`)}</p>
    </Card>
  );
}

// ---------------------------------------------------------------- new document
export function NewDocumentPage({ ui, extraFields }: { ui: ProductUi; extraFields?: (v: { notes: string; setNotes: (s: string) => void }) => ReactNode }) {
  const { t } = useTranslation();
  const nav = useNavigate();
  const toast = useToast();
  const errMsg = useErrorMessage();
  const api = productApi(ui.route);
  const [clientRef] = useState(uuid);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [progress, setProgress] = useState<Partial<Record<Side, number | null>>>({});
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [phoneReq, setPhoneReq] = useState<{ id: string; side: Side } | null>(null);

  // Waiting for the phone: poll the request; once done, reload the document to show the photo.
  useEffect(() => {
    if (!phoneReq || !doc) return;
    const h = window.setInterval(async () => {
      try {
        const r = await captureApi.get(phoneReq.id);
        if (r.status === "pending") return;
        setPhoneReq(null);
        if (r.status === "done") setDoc(await api.get(doc.id));
      } catch (e) { setError(errMsg(e)); setPhoneReq(null); }
    }, 2000);
    return () => window.clearInterval(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phoneReq, doc?.id]);
  const askPhone = async (side: Side) => {
    setError(null);
    try {
      const d = await ensureDoc();
      const r = await captureApi.create(d.id, side);
      setPhoneReq({ id: r.id, side });
    } catch (e) { setError(errMsg(e)); }
  };
  const cancelPhone = () => { if (phoneReq) void captureApi.finish(phoneReq.id, "cancel").catch(() => {}); setPhoneReq(null); };

  const ensureDoc = async () => {
    if (doc) return doc;
    // client_ref makes creation idempotent if the request is retried
    const d = await api.create({ title: title || undefined, notes: notes || undefined, client_ref: clientRef });
    setDoc(d);
    return d;
  };
  const upload = async (side: Side, file: File) => {
    setError(null);
    try {
      const d = await ensureDoc();
      setProgress((p) => ({ ...p, [side]: 0 }));
      const updated = await api.upload(d.id, side, file, (pct) => setProgress((p) => ({ ...p, [side]: pct })));
      setDoc(updated);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setProgress((p) => ({ ...p, [side]: null }));
    }
  };
  const remove = async (side: Side) => {
    if (!doc) return;
    try { setDoc(await api.removeImage(doc.id, side)); } catch (e) { setError(errMsg(e)); }
  };
  const run = async (langs: string[] | null) => {
    if (!doc) return;
    setRunning(true);
    setError(null);
    try {
      if (title !== (doc.title ?? "") || notes !== (doc.notes ?? "")) await api.updateMeta(doc.id, { title: title || null, notes: notes || null });
      const r = await api.process(doc.id, { languages: langs });
      if (r.status === "completed") nav(`/documents/${doc.id}`);
      else setJobId(r.job_id);
    } catch (e) {
      setError(errMsg(e));
      setRunning(false);
    }
  };
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <div className="flex items-center gap-2">
        <Link to="/" aria-label={t("common.back")} className="rounded-md p-1 hover:bg-surface-2"><ArrowLeft className="size-5 rtl:-scale-x-100" /></Link>
        <h1 className="text-2xl font-semibold">{t(`${ui.i18nKey}.new`)}</h1>
      </div>
      <Card className="grid gap-3 p-4 md:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">{t(`${ui.i18nKey}.titleLabel`)}
          <input className="input" dir="auto" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} />
        </label>
        {extraFields?.({ notes, setNotes })}
      </Card>
      <div className={cx("grid gap-4", ui.sides.length > 1 && "md:grid-cols-2")}>
        {ui.sides.map((s) => (
          <UploadSlot key={s.side} route={ui.route} side={s.side} optional={s.optional} image={doc?.images.find((i) => i.side === s.side)}
            progress={progress[s.side]} onFile={(f) => upload(s.side, f)} onRemove={() => remove(s.side)} disabled={running || (!!phoneReq && phoneReq.side !== s.side)}
            onPhone={() => askPhone(s.side)} phoneWaiting={phoneReq?.side === s.side} onCancelPhone={cancelPhone} />
        ))}
      </div>
      {error && <Alert tone="danger">{error}</Alert>}
      <Card className="p-4">
        <ProcessPanel hasImages={!!doc?.images.length} status={doc?.status ?? "draft"} jobId={jobId} processed={false} busy={running && !jobId}
          onRun={(langs) => run(langs)}
          onDone={(j) => { setRunning(false); if (j.status === "completed") { toast("success", t("process.done")); nav(`/documents/${doc!.id}`); } }} />
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------- document workspace
export interface WorkspaceRenderProps<D> {
  doc: DocumentOut<D>;
  data: D;
  actions: FieldActions & { patch: (changes: FieldChange[]) => Promise<void> };
  selected: string[];
}

export function DocumentWorkspace<D extends { warnings: string[] }>({ ui, renderFields, renderAside, renderHeaderExtras }: {
  ui: ProductUi;
  renderFields: (p: WorkspaceRenderProps<D>) => ReactNode;
  renderAside?: (p: WorkspaceRenderProps<D>) => ReactNode;
  renderHeaderExtras?: (doc: DocumentOut<D>) => ReactNode;
}) {
  const { id } = useParams();
  const { t } = useTranslation();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const errMsg = useErrorMessage();
  const api = productApi(ui.route);
  const docQ = useDocument<D>(ui.route, id);
  const history = useQuery({ queryKey: [ui.route, "history", id, docQ.data?.version], queryFn: () => api.history(id!), enabled: !!id });
  const [side, setSide] = useState<Side>("front");
  const [selected, setSelected] = useState<string[]>([]);
  const [tab, setTab] = useState<"fields" | "ocr" | "history" | "job">("fields");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const doc = docQ.data;

  useEffect(() => {
    if (doc && !doc.images.some((i) => i.side === side) && doc.images[0]) setSide(doc.images[0].side);
  }, [doc, side]);

  const refresh = (updated: DocumentOut) => qc.setQueryData([ui.route, "doc", id], updated);
  const patch = async (changes: FieldChange[]) => {
    try {
      refresh(await api.patchFields(id!, changes, doc?.version));
      toast("success", t("fields.saved"));
    } catch (e) {
      if ((e as { code?: string }).code === "version_conflict") qc.invalidateQueries({ queryKey: [ui.route, "doc", id] });
      throw e;
    }
  };
  const actions = useMemo(() => ({
    patch,
    onSet: (path: string, value: unknown) => patch([{ path, value }]),
    onVerify: async (path: string) => { try { await patch([{ path, op: "verify" }]); } catch (e) { toast("danger", errMsg(e)); } },
    onLocate: (ids: string[]) => {
      setSelected(ids);
      const line = doc?.ocr?.flatMap((p) => p.lines).find((l) => ids.includes(l.id));
      if (line) setSide(line.side);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [doc?.version, doc?.ocr]);
  const del = useMutation({ mutationFn: () => api.remove(id!), onSuccess: () => { toast("success", t("delete.done")); qc.invalidateQueries({ queryKey: [ui.route] }); nav("/history"); }, onError: (e) => toast("danger", errMsg(e)) });
  const review = useMutation({ mutationFn: (s: string) => api.review(id!, s), onSuccess: refresh, onError: (e) => toast("danger", errMsg(e)) });

  if (docQ.isLoading) return <Spinner />;
  if (docQ.isError || !doc) return <Alert tone="danger" action={<Button size="sm" onClick={() => docQ.refetch()}>{t("common.retry")}</Button>}>{errMsg(docQ.error)}</Alert>;

  const onSelectLine = (lid: string) => {
    setSelected([lid]);
    setTab("ocr");
  };
  const props: WorkspaceRenderProps<D> | null = doc.data ? { doc, data: doc.data, actions, selected } : null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/history" aria-label={t("common.back")} className="rounded-md p-1 hover:bg-surface-2"><ArrowLeft className="size-5 rtl:-scale-x-100" /></Link>
        <h1 className="text-xl font-semibold"><Bidi>{doc.title || ui.docTitle(doc as unknown as DocumentOut) || t("common.unknown")}</Bidi></h1>
        <StatusBadge status={doc.status} />
        <ReviewBadge status={doc.review_status} />
        <div className="ms-auto flex flex-wrap gap-2">
          {renderHeaderExtras?.(doc)}
          {doc.data && <ExportMenu formats={ui.exportFormats} onExport={(f) => api.download(`/${ui.route}/${doc.id}/export?format=${f}`, `${ui.route}.${f}`)} />}
          <Button variant="ghost" onClick={() => setConfirmDelete(true)}><Trash2 className="size-4" aria-hidden />{t("common.delete")}</Button>
        </div>
      </div>
      {doc.data?.warnings?.length ? <WarningList warnings={doc.data.warnings} /> : null}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-3">
          <ImageViewer route={ui.route} images={doc.images} pages={doc.ocr ?? []} side={side} onSideChange={setSide} selected={selected} onSelectLine={onSelectLine} regionLabel={ui.regionLabel} />
          <Card className="p-4">
            <ProcessPanel hasImages={doc.images.length > 0} status={doc.status} jobId={jobId} processed={!!doc.data}
              onRun={async (langs, force) => { try { const r = await api.process(doc.id, { languages: langs, force }); setJobId(r.job_id); qc.invalidateQueries({ queryKey: [ui.route, "doc", id] }); } catch (e) { toast("danger", errMsg(e)); } }}
              onDone={() => qc.invalidateQueries({ queryKey: [ui.route, "doc", id] })} />
          </Card>
          {props && renderAside?.(props)}
        </div>
        <div className="flex min-w-0 flex-col gap-3">
          <div role="tablist" className="flex gap-1 overflow-x-auto border-b border-line">
            {(["fields", "ocr", "history", "job"] as const).map((k) => (
              <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)} className={cx("whitespace-nowrap border-b-2 px-3 py-2 text-sm", tab === k ? "border-accent font-medium text-ink" : "border-transparent text-ink-2 hover:text-ink")}>{t(`tabs.${k}`)}</button>
            ))}
          </div>
          <div role="tabpanel">
            {tab === "fields" && (props ? (
              <div className="flex flex-col gap-3">
                {renderFields(props)}
                <div className="flex flex-wrap gap-2 border-t border-line pt-3">
                  <Button variant="primary" onClick={() => review.mutate("verified")} loading={review.isPending}>{t("review.markVerified")}</Button>
                  <Button onClick={() => review.mutate("needs_review")}>{t("review.markNeeds")}</Button>
                </div>
                <p className="text-xs text-ink-3">{t("confidence.disclaimer")}</p>
              </div>
            ) : <EmptyState title={t(`status.${doc.status}`)} body={t("upload.required")} />)}
            {tab === "ocr" && <OcrTextPanel pages={doc.ocr ?? []} selected={selected} onSelect={(l) => { setSelected([l]); const line = doc.ocr?.flatMap((p) => p.lines).find((x) => x.id === l); if (line) setSide(line.side); }} />}
            {tab === "history" && <HistoryPanel events={history.data} />}
            {tab === "job" && <JobDetails job={doc.latest_job} />}
          </div>
        </div>
      </div>
      <ConfirmDialog open={confirmDelete} title={t("delete.title")} body={t("delete.body")} confirmLabel={t("common.delete")} danger busy={del.isPending}
        onCancel={() => setConfirmDelete(false)} onConfirm={() => del.mutate()} />
    </div>
  );
}

// ---------------------------------------------------------------- settings
export function SettingsPage() {
  const { t, i18n } = useTranslation();
  const qc = useQueryClient();
  const toast = useToast();
  const errMsg = useErrorMessage();
  const me = useQuery({ queryKey: ["me"], queryFn: accountApi.me });
  const models = useQuery({ queryKey: ["models"], queryFn: accountApi.models });
  const [region, setRegion] = useState("");
  useEffect(() => { setRegion(me.data?.default_phone_region ?? ""); }, [me.data]);
  const save = async () => {
    try {
      const r = await accountApi.updateMe({ default_phone_region: region.trim() || null });
      qc.setQueryData(["me"], r);
      toast("success", t("fields.saved"));
    } catch (e) { toast("danger", errMsg(e)); }
  };
  const [android, setAndroid] = useState("");
  useEffect(() => { setAndroid(me.data?.android_app_url ?? ""); }, [me.data]);
  const saveAndroid = async () => {
    try {
      const r = await accountApi.updateWorkspaceSettings({ android_app_url: android.trim() || null });
      qc.setQueryData(["me"], r);
      toast("success", t("fields.saved"));
    } catch (e) { toast("danger", errMsg(e)); }
  };
  const isOwner = me.data?.role === "owner";
  const usage = useQuery({ queryKey: ["usage"], queryFn: accountApi.usage, staleTime: 30_000 });
  const ocr = (models.data?.ocr as { provider: string; available: boolean; reason: string | null; models: { task: string; name: string; version: string | null }[] }[] | undefined) ?? [];
  const caps = (models.data?.capabilities as Record<string, string> | undefined) ?? {};
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-5">
      <h1 className="text-2xl font-semibold">{t("settings.title")}</h1>
      <Card className="p-5">
        <h2 className="mb-3 font-semibold">{t("settings.account")}</h2>
        {me.data ? <p className="text-sm"><span dir="ltr">{me.data.email}</span> · {me.data.workspace_name}</p> : <Spinner />}
      </Card>
      <Card className="flex flex-col gap-3 p-5">
        <h2 className="font-semibold">{t("settings.preferences")}</h2>
        <div className="flex flex-wrap items-center gap-4"><LanguageSelectorProxy /><ThemeToggleProxy /></div>
        <label className="flex max-w-sm flex-col gap-1 text-sm">{t("settings.phoneRegion")}
          <input className="input" dir="ltr" maxLength={2} value={region} onChange={(e) => setRegion(e.target.value.toUpperCase())} placeholder="MA" aria-describedby="region-hint" />
          <span id="region-hint" className="text-xs text-ink-3">{t("settings.phoneRegionHint")}</span>
        </label>
        <div><Button variant="primary" onClick={save}>{t("common.save")}</Button></div>
      </Card>
      <Card className="flex flex-col gap-4 p-5">
        <div className="flex items-center justify-between gap-2">
          <h2 className="font-semibold">{t("usage.title")}</h2>
          <Button size="sm" variant="ghost" onClick={() => usage.refetch()}>{t("common.refresh")}</Button>
        </div>
        {usage.isLoading ? <Spinner /> : usage.isError || !usage.data ? <Alert tone="warning">{t("errors.generic")}</Alert> : (
          <>
            <UsageBar label={t("usage.database")} used={usage.data.database.used_bytes} limit={usage.data.database.limit_bytes} bytes />
            <UsageBar label={t("usage.storage")} used={usage.data.storage.used_bytes} limit={usage.data.storage.limit_bytes} bytes estimated />
            <UsageBar label={t("usage.ollamaWeek")} used={usage.data.ollama.requests_7d} limit={usage.data.ollama.limit_week} hint={t("usage.ollamaWeekHint")} />
            {usage.data.ollama.limit_day ? <UsageBar label={t("usage.ollamaDay")} used={usage.data.ollama.requests_today} limit={usage.data.ollama.limit_day} /> : null}
            {usage.data.ollama.limit_month ? <UsageBar label={t("usage.ollamaMonth")} used={usage.data.ollama.requests_month} limit={usage.data.ollama.limit_month} /> : null}
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-4">
              <div><dt className="text-xs text-ink-3">{t("usage.documents")}</dt><dd className="font-medium">{formatNumber(usage.data.documents.active, i18n.language)}</dd></div>
              <div><dt className="text-xs text-ink-3">{t("usage.ollamaDay")}</dt><dd className="font-medium">{formatNumber(usage.data.ollama.requests_today, i18n.language)}</dd></div>
              <div><dt className="text-xs text-ink-3">{t("usage.ollamaMonth")}</dt><dd className="font-medium">{formatNumber(usage.data.ollama.requests_month, i18n.language)}</dd></div>
              <div><dt className="text-xs text-ink-3">{t("usage.keys")}</dt><dd className="font-medium">{usage.data.ollama.keys}</dd></div>
              <div><dt className="text-xs text-ink-3">{t("usage.model")}</dt><dd className="font-mono text-xs" dir="ltr">{usage.data.ollama.model ?? "—"}</dd></div>
            </dl>
            <p className="text-xs text-ink-3">{t("usage.note", { mb: usage.data.vercel.max_request_mb, s: usage.data.vercel.function_timeout_s })}</p>
          </>
        )}
      </Card>
      <Card className="flex flex-col gap-3 p-5">
        <h2 className="flex items-center gap-2 font-semibold"><AndroidIcon className="size-5 text-[#3DDC84]" />{t("settings.androidTitle")}</h2>
        <label className="flex flex-col gap-1 text-sm">{t("settings.androidUrl")}
          <input className="input" type="url" dir="ltr" inputMode="url" value={android} disabled={!isOwner}
            onChange={(e) => setAndroid(e.target.value)} placeholder="https://…/BusinessCardScanner.apk" aria-describedby="android-hint" />
          <span id="android-hint" className="text-xs text-ink-3">{isOwner ? t("settings.androidHint") : t("settings.ownerOnly")}</span>
        </label>
        {isOwner && <div><Button variant="primary" onClick={saveAndroid}>{t("common.save")}</Button></div>}
      </Card>
      <Card className="flex flex-col gap-3 p-5">
        <h2 className="font-semibold">{t("settings.models")}</h2>
        {models.isLoading ? <Spinner /> : (
          <ul className="flex flex-col gap-2 text-sm">
            {ocr.map((p) => (
              <li key={p.provider} className="rounded-lg border border-line p-3">
                <p className="font-medium" dir="ltr">{p.provider} — <span className={p.available ? "text-emerald-600" : "text-ink-3"}>{p.available ? t("settings.available") : t("settings.unavailable")}</span></p>
                {p.reason && <p className="text-xs text-ink-3" dir="ltr">{p.reason}</p>}
                {(p.models?.length ?? 0) > 0 && <p className="mt-1 font-mono text-xs text-ink-2" dir="ltr">{(p.models ?? []).map((m) => `${m.task}: ${m.name}`).join(" · ")}</p>}
              </li>
            ))}
          </ul>
        )}
        {Object.keys(caps).length > 0 && (
          <div>
            <p className="mb-1 text-sm font-medium">{t("settings.capabilities")}</p>
            <ul className="text-xs text-ink-2" dir="ltr">{Object.entries(caps).map(([k, v]) => <li key={k}><span className="font-mono">{k}</span>: {v}</li>)}</ul>
          </div>
        )}
      </Card>
      <Card className="p-5">
        <h2 className="mb-2 font-semibold">{t("settings.privacy")}</h2>
        <p className="text-sm text-ink-2">{ocr.some((p) => p.provider === "ollama") ? t("settings.privacyTextCloud") : t("settings.privacyText")}</p>
      </Card>
    </div>
  );
}

function formatBytes(n: number, lang: string): string {
  const units = ["B", "KB", "MB", "GB"];
  let v = n, i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${new Intl.NumberFormat(lang, { maximumFractionDigits: v < 10 && i > 0 ? 1 : 0 }).format(v)} ${units[i]}`;
}

/** One quota line: used / limit with a coloured bar (amber ≥ 75 %, red ≥ 90 %). Unknown limit → value only. */
function UsageBar({ label, used, limit, bytes, estimated, hint }: { label: string; used: number | null; limit: number | null; bytes?: boolean; estimated?: boolean; hint?: string }) {
  const { t, i18n } = useTranslation();
  const fmt = (n: number) => (bytes ? formatBytes(n, i18n.language) : formatNumber(n, i18n.language));
  const pct = used != null && limit ? Math.min(100, (used / limit) * 100) : null;
  const tone = pct == null ? "bg-accent" : pct >= 90 ? "bg-red-500" : pct >= 75 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-2 text-sm">
        <span className="font-medium">{label}{estimated && <span className="ms-1 text-xs font-normal text-ink-3">({t("usage.estimated")})</span>}</span>
        <span className="tabular-nums text-ink-2" dir="ltr">
          {used == null ? "—" : fmt(used)}{limit ? ` / ${fmt(limit)}` : ""}{pct != null && ` · ${Math.round(pct)} %`}
        </span>
      </div>
      {limit ? (
        <div className="h-2 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct == null ? undefined : Math.round(pct)}>
          <div className={cx("h-full rounded-full transition-all", tone)} style={{ width: `${pct ?? 0}%` }} />
        </div>
      ) : <p className="text-xs text-ink-3">{t("usage.noLimit")}</p>}
      {hint && <p className="text-xs text-ink-3">{hint}</p>}
    </div>
  );
}

