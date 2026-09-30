import { ZoomIn, ZoomOut, Maximize } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ImageInfo, OcrPage, Side } from "@ocr/shared-types";
import type { ProductRoute } from "../lib/api";
import { useAuthedImage } from "../lib/hooks";
import { Button, cx } from "./primitives";

const REGION_COLORS: Record<string, string> = {
  address: "#2563eb", logo: "#db2777", qr: "#0891b2", text_block: "#64748b",
};

/**
 * Shows the *processed* image (the one OCR coordinates refer to) with line boxes and candidate
 * regions. Clicking a line selects it; selected ids are highlighted (driven by the fields panel).
 */
export function ImageViewer({ route, images, pages, side, onSideChange, selected, onSelectLine, regionLabel }: {
  route: ProductRoute;
  images: ImageInfo[];
  pages: OcrPage[];
  side: Side;
  onSideChange?: (s: Side) => void;
  selected: string[];
  onSelectLine?: (id: string) => void;
  regionLabel?: (label: string) => string;
}) {
  const { t } = useTranslation();
  const [zoom, setZoom] = useState(1);
  const [showLines, setShowLines] = useState(true);
  const [showRegions, setShowRegions] = useState(true);
  const img = images.find((i) => i.side === side);
  const processed = !!img?.processed_url;
  const { url } = useAuthedImage(route, img ? img.processed_url ?? img.url : null);
  const page = pages.find((p) => p.side === side);
  const w = (processed ? img?.processed_width : img?.width) ?? page?.width ?? 1;
  const h = (processed ? img?.processed_height : img?.height) ?? page?.height ?? 1;
  const sides = images.map((i) => i.side).sort((a) => (a === "front" ? -1 : 1));

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        {sides.length > 1 && (
          <div role="tablist" aria-label={t("viewer.sides")} className="inline-flex rounded-lg border border-line bg-surface p-0.5">
            {sides.map((s) => (
              <button key={s} role="tab" aria-selected={s === side} onClick={() => onSideChange?.(s)} className={cx("rounded-md px-3 py-1 text-sm", s === side ? "bg-accent text-accent-fg" : "text-ink-2")}>{t(`upload.${s}`)}</button>
            ))}
          </div>
        )}
        <label className="inline-flex items-center gap-1 text-xs text-ink-2"><input type="checkbox" checked={showLines} onChange={(e) => setShowLines(e.target.checked)} />{t("viewer.lines")}</label>
        <label className="inline-flex items-center gap-1 text-xs text-ink-2"><input type="checkbox" checked={showRegions} onChange={(e) => setShowRegions(e.target.checked)} />{t("viewer.regions")}</label>
        <div className="ms-auto flex gap-1">
          <Button size="sm" variant="ghost" aria-label={t("viewer.zoomOut")} onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}><ZoomOut className="size-4" /></Button>
          <Button size="sm" variant="ghost" aria-label={t("viewer.reset")} onClick={() => setZoom(1)}><Maximize className="size-4" /></Button>
          <Button size="sm" variant="ghost" aria-label={t("viewer.zoomIn")} onClick={() => setZoom((z) => Math.min(4, z + 0.25))}><ZoomIn className="size-4" /></Button>
        </div>
      </div>
      <div className="max-h-[70vh] overflow-auto rounded-xl border border-line bg-[repeating-conic-gradient(var(--surface-2)_0_25%,var(--surface)_0_50%)] bg-[length:16px_16px]" dir="ltr">
        {!img ? (
          <p className="p-10 text-center text-sm text-ink-3">{t("viewer.noImage")}</p>
        ) : (
          <div className="relative" style={{ width: `${zoom * 100}%` }}>
            {url ? <img src={url} alt={t(`upload.${side}`)} className="block w-full" /> : <div className="aspect-[16/10] w-full animate-pulse bg-surface-2" />}
            {processed && page && (
              <svg viewBox={`0 0 ${w} ${h}`} className="absolute inset-0 size-full" role="group" aria-label={t("viewer.lines")}>
                {showRegions && page.regions.map((r) => (
                  <g key={r.id}>
                    <rect x={r.bbox.x} y={r.bbox.y} width={r.bbox.w} height={r.bbox.h} fill="none" stroke={REGION_COLORS[r.label ?? "text_block"] ?? "#64748b"} strokeWidth={Math.max(2, w / 400)} strokeDasharray="10 6" />
                    <text x={r.bbox.x + 4} y={r.bbox.y + Math.max(14, w / 70)} fontSize={Math.max(12, w / 70)} fill={REGION_COLORS[r.label ?? "text_block"] ?? "#64748b"} fontWeight={600}>
                      {(regionLabel?.(r.label ?? "") ?? r.label) + (r.confidence != null ? ` ${Math.round(r.confidence * 100)}%` : "")} · {t("viewer.candidate")}
                    </text>
                  </g>
                ))}
                {showLines && page.lines.map((l) => {
                  const sel = selected.includes(l.id);
                  return (
                    <rect key={l.id} x={l.bbox.x} y={l.bbox.y} width={l.bbox.w} height={l.bbox.h} rx={3}
                      className="cursor-pointer" onClick={() => onSelectLine?.(l.id)}
                      fill={sel ? "rgba(250, 204, 21, 0.35)" : "rgba(59, 130, 246, 0.08)"} stroke={sel ? "#ca8a04" : "rgba(59,130,246,0.7)"} strokeWidth={sel ? Math.max(3, w / 300) : Math.max(1, w / 900)}>
                      <title>{l.text}</title>
                    </rect>
                  );
                })}
              </svg>
            )}
          </div>
        )}
      </div>
      {img && !processed && <p className="text-xs text-ink-3">{t("viewer.original")}</p>}
    </div>
  );
}
