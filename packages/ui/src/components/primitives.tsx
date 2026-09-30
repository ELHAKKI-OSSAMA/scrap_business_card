import { AlertTriangle, CheckCircle2, Info, Loader2, X } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { DocStatus, ExtractionMethod, ReviewStatus } from "@ocr/shared-types";
import { formatPercent } from "../lib/format";

export function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(" ");
}

type Variant = "primary" | "secondary" | "ghost" | "danger";
export function Button({ variant = "secondary", size = "md", loading, className, children, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: "sm" | "md"; loading?: boolean }) {
  const base = "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-50 disabled:cursor-not-allowed";
  const sizes = { sm: "h-8 px-3 text-sm", md: "h-10 px-4 text-sm" };
  const variants: Record<Variant, string> = {
    primary: "bg-accent text-accent-fg hover:bg-accent-strong shadow-sm",
    secondary: "border border-line bg-surface text-ink hover:bg-surface-2",
    ghost: "text-ink-2 hover:bg-surface-2",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };
  return (
    <button className={cx(base, sizes[size], variants[variant], className)} disabled={loading || rest.disabled} {...rest}>
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function Card({ className, children, ...rest }: { className?: string; children: ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cx("rounded-xl border border-line bg-surface shadow-sm", className)} {...rest}>{children}</div>;
}

export function Spinner({ label }: { label?: string }) {
  const { t } = useTranslation();
  return (
    <div role="status" className="flex items-center gap-2 text-ink-2">
      <Loader2 className="size-5 animate-spin" aria-hidden />
      <span>{label ?? t("common.loading")}</span>
    </div>
  );
}

const tone = {
  neutral: "bg-surface-2 text-ink-2 border-line",
  info: "bg-sky-50 text-sky-800 border-sky-200 dark:bg-sky-950 dark:text-sky-200 dark:border-sky-800",
  success: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-200 dark:border-emerald-800",
  warning: "bg-amber-50 text-amber-900 border-amber-200 dark:bg-amber-950 dark:text-amber-200 dark:border-amber-800",
  danger: "bg-red-50 text-red-800 border-red-200 dark:bg-red-950 dark:text-red-200 dark:border-red-800",
  accent: "bg-accent-soft text-accent-ink border-transparent",
};
export type Tone = keyof typeof tone;

export function Badge({ tone: tn = "neutral", children, title, className }: { tone?: Tone; children: ReactNode; title?: string; className?: string }) {
  return <span title={title} className={cx("inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium", tone[tn], className)}>{children}</span>;
}

export function StatusBadge({ status }: { status: DocStatus | string }) {
  const { t } = useTranslation();
  const map: Record<string, Tone> = { draft: "neutral", ready: "info", queued: "info", processing: "info", running: "info", completed: "success", failed: "danger" };
  return <Badge tone={map[status] ?? "neutral"}>{(status === "processing" || status === "queued" || status === "running") && <Loader2 className="size-3 animate-spin" aria-hidden />}{t(`status.${status}`)}</Badge>;
}

export function ReviewBadge({ status }: { status: ReviewStatus | string }) {
  const { t } = useTranslation();
  const map: Record<string, Tone> = { unreviewed: "neutral", needs_review: "warning", verified: "success", corrected: "accent", rejected: "danger" };
  return <Badge tone={map[status] ?? "neutral"}>{t(`review.${status}`)}</Badge>;
}

export function ConfidenceBadge({ value }: { value: number | null | undefined }) {
  const { t, i18n } = useTranslation();
  if (value === null || value === undefined) return <Badge title={t("confidence.disclaimer")}>{t("confidence.none")}</Badge>;
  const level = value >= 0.85 ? "high" : value >= 0.6 ? "medium" : "low";
  const tn: Tone = level === "high" ? "success" : level === "medium" ? "warning" : "danger";
  return (
    <Badge tone={tn} title={`${t("confidence.label")}: ${formatPercent(value, i18n.language)} — ${t("confidence.disclaimer")}`}>
      <span className="sr-only">{t("confidence.label")}: </span>
      {formatPercent(value, i18n.language)}
    </Badge>
  );
}

export function MethodChip({ method }: { method: ExtractionMethod }) {
  const { t } = useTranslation();
  return <Badge tone={method === "manual" ? "accent" : method === "llm" ? "warning" : "neutral"}>{t(`method.${method}`)}</Badge>;
}

export function EmptyState({ icon, title, body, action }: { icon?: ReactNode; title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-line px-6 py-14 text-center">
      {icon && <div className="text-ink-3">{icon}</div>}
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {body && <p className="max-w-md text-sm text-ink-2">{body}</p>}
      {action}
    </div>
  );
}

export function Alert({ tone: tn = "info", title, children, action }: { tone?: "info" | "warning" | "danger" | "success"; title?: string; children?: ReactNode; action?: ReactNode }) {
  const Icon = tn === "success" ? CheckCircle2 : tn === "info" ? Info : AlertTriangle;
  return (
    <div role={tn === "danger" ? "alert" : "status"} className={cx("flex items-start gap-3 rounded-lg border p-3 text-sm", tone[tn])}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className={title ? "mt-0.5" : ""}>{children}</div>}
      </div>
      {action}
    </div>
  );
}

/** Confirmation dialog built on the native <dialog> element (focus trap + Esc for free). */
export function ConfirmDialog({ open, title, body, confirmLabel, danger, onConfirm, onCancel, busy }: { open: boolean; title: string; body?: ReactNode; confirmLabel: string; danger?: boolean; onConfirm: () => void; onCancel: () => void; busy?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  const { t } = useTranslation();
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) (d.showModal ? d.showModal() : d.setAttribute("open", ""));
    if (!open && d.open) (d.close ? d.close() : d.removeAttribute("open"));
  }, [open]);
  return (
    <dialog ref={ref} onCancel={(e) => { e.preventDefault(); onCancel(); }} aria-labelledby="confirm-title" className="m-auto w-[min(28rem,calc(100vw-2rem))] rounded-xl border border-line bg-surface p-0 text-ink shadow-xl backdrop:bg-black/40">
      <div className="p-5">
        <h2 id="confirm-title" className="text-lg font-semibold">{title}</h2>
        {body && <div className="mt-2 text-sm text-ink-2">{body}</div>}
      </div>
      <div className="flex justify-end gap-2 border-t border-line bg-surface-2 px-5 py-3">
        <Button onClick={onCancel}>{t("common.cancel")}</Button>
        <Button variant={danger ? "danger" : "primary"} onClick={onConfirm} loading={busy}>{confirmLabel}</Button>
      </div>
    </dialog>
  );
}

// ---------------------------------------------------------------- toasts
type Toast = { id: number; tone: "success" | "danger" | "info"; text: string };
const ToastCtx = createContext<(tone: Toast["tone"], text: string) => void>(() => undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((tn: Toast["tone"], text: string) => {
    const id = Date.now() + Math.random();
    setItems((xs) => [...xs, { id, tone: tn, text }]);
    setTimeout(() => setItems((xs) => xs.filter((x) => x.id !== id)), 5000);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed bottom-4 end-4 z-50 flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2">
        {items.map((x) => (
          <div key={x.id} className={cx("pointer-events-auto flex items-start gap-2 rounded-lg border p-3 text-sm shadow-lg", tone[x.tone === "danger" ? "danger" : x.tone === "success" ? "success" : "info"])}>
            <span className="flex-1">{x.text}</span>
            <button aria-label="close" onClick={() => setItems((xs) => xs.filter((y) => y.id !== x.id))}><X className="size-4" /></button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);

/** Renders user/OCR content with automatic direction so Arabic inside LTR UI (and vice versa) displays correctly. */
export function Bidi({ children, className, as: Tag = "bdi" }: { children: ReactNode; className?: string; as?: "bdi" | "span" | "p" | "div" }) {
  return <Tag dir="auto" className={className}>{children}</Tag>;
}
