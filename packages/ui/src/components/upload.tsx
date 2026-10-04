import { Camera, ImagePlus, Monitor, RefreshCw, Smartphone, Trash2, X } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";
import { useTranslation } from "react-i18next";
import type { ImageInfo, Side } from "@ocr/shared-types";
import { useAuthedImage } from "../lib/hooks";
import type { ProductRoute } from "../lib/api";
import { Button, cx } from "./primitives";

export const ACCEPT = "image/jpeg,image/png,image/webp,image/tiff";
const MAX_MB = 15;

const coarsePointer = () => typeof window !== "undefined" && !!window.matchMedia?.("(pointer: coarse)").matches;

export function Dropzone({ onFiles, multiple, disabled, label, onPhone, phoneWaiting, onCancelPhone }: {
  onFiles: (files: File[]) => void; multiple?: boolean; disabled?: boolean; label?: string;
  /** PC only: ask the signed-in phone to take the photo instead of picking a file. */
  onPhone?: () => void; phoneWaiting?: boolean; onCancelPhone?: () => void;
}) {
  const { t } = useTranslation();
  const [over, setOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const camRef = useRef<HTMLInputElement>(null);
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    if (disabled) return;
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type.startsWith("image/"));
    if (files.length) onFiles(multiple ? files : files.slice(0, 1));
  };
  if (phoneWaiting) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-accent bg-accent-soft p-6 text-center">
        <Smartphone className="size-8 animate-pulse text-accent-ink" aria-hidden />
        <p className="font-medium text-ink">{t("upload.phoneWaiting")}</p>
        <p className="text-xs text-ink-2">{t("upload.phoneWaitingHint")}</p>
        <Button type="button" size="sm" variant="ghost" onClick={onCancelPhone}><X className="size-4" aria-hidden />{t("common.cancel")}</Button>
      </div>
    );
  }
  const phoneChoice = onPhone && !coarsePointer();
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={cx("flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 text-center transition-colors", over ? "border-accent bg-accent-soft" : "border-line bg-surface-2", disabled && "opacity-60")}
    >
      <ImagePlus className="size-8 text-ink-3" aria-hidden />
      {label && <p className="font-medium text-ink">{label}</p>}
      <p className="text-sm text-ink-2">
        {t("upload.drop")}{" "}
        <button type="button" className="font-medium text-accent-ink underline" onClick={() => fileRef.current?.click()} disabled={disabled}>{t("upload.browse")}</button>
      </p>
      {phoneChoice ? (
        <div className="flex flex-wrap justify-center gap-2">
          <Button type="button" size="sm" variant="secondary" onClick={() => fileRef.current?.click()} disabled={disabled}><Monitor className="size-4" aria-hidden />{t("upload.fromPc")}</Button>
          <Button type="button" size="sm" onClick={onPhone} disabled={disabled}><Smartphone className="size-4" aria-hidden />{t("upload.fromPhone")}</Button>
        </div>
      ) : (
        <Button type="button" size="sm" onClick={() => camRef.current?.click()} disabled={disabled}><Camera className="size-4" aria-hidden />{t("upload.camera")}</Button>
      )}
      <p className="text-xs text-ink-3">{t("upload.formats", { mb: MAX_MB })}</p>
      <input ref={fileRef} type="file" accept={ACCEPT} multiple={multiple} className="sr-only" tabIndex={-1} aria-hidden
        onChange={(e) => { const f = Array.from(e.target.files ?? []); if (f.length) onFiles(f); e.target.value = ""; }} />
      {/* capture=environment opens the rear camera on mobile browsers */}
      <input ref={camRef} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden
        onChange={(e) => { const f = Array.from(e.target.files ?? []); if (f.length) onFiles(f.slice(0, 1)); e.target.value = ""; }} />
    </div>
  );
}

export function UploadSlot({ route, side, image, optional, progress, onFile, onRemove, disabled, onPhone, phoneWaiting, onCancelPhone }: {
  route: ProductRoute; side: Side; image?: ImageInfo; optional?: boolean; progress?: number | null; onFile: (f: File) => void; onRemove?: () => void; disabled?: boolean;
  onPhone?: () => void; phoneWaiting?: boolean; onCancelPhone?: () => void;
}) {
  const { t } = useTranslation();
  const { url } = useAuthedImage(route, image ? `${image.url.replace("variant=original", "variant=thumb")}` : null);
  const inputRef = useRef<HTMLInputElement>(null);
  const title = `${t(`upload.${side}`)}${optional ? ` (${t("upload.optional")})` : ""}`;
  return (
    <section aria-label={title} className="flex flex-col gap-2">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {image ? (
        <div className="relative overflow-hidden rounded-xl border border-line bg-surface-2">
          {url ? <img src={url} alt={title} className="mx-auto max-h-64 object-contain" /> : <div className="h-40 animate-pulse" />}
          <div className="flex items-center justify-between gap-2 border-t border-line bg-surface px-3 py-2 text-xs text-ink-2">
            <span dir="ltr">{image.width}×{image.height}</span>
            <div className="flex gap-1">
              <Button size="sm" variant="ghost" onClick={() => inputRef.current?.click()} disabled={disabled}><RefreshCw className="size-3.5" aria-hidden />{t("upload.replace")}</Button>
              {onRemove && <Button size="sm" variant="ghost" onClick={onRemove} disabled={disabled} aria-label={t("upload.remove")}><Trash2 className="size-3.5" aria-hidden /></Button>}
            </div>
          </div>
          <input ref={inputRef} type="file" accept={ACCEPT} className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = ""; }} />
        </div>
      ) : (
        <Dropzone onFiles={(f) => onFile(f[0])} disabled={disabled} onPhone={onPhone} phoneWaiting={phoneWaiting} onCancelPhone={onCancelPhone} />
      )}
      {progress !== null && progress !== undefined && (
        <div role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label={t("upload.uploading", { pct: progress })} className="h-2 overflow-hidden rounded-full bg-surface-2">
          <div className="h-full bg-accent transition-all" style={{ width: `${progress}%` }} />
        </div>
      )}
    </section>
  );
}
