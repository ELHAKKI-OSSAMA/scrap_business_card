import { Layers } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Card, Dropzone, StatusBadge, productApi, useErrorMessage, uuid } from "@ocr/ui";

type Item = { name: string; id?: string; status: string; error?: string; pct?: number };

/** Several single-sided cards at once: one record per image, processed independently. */
export function BatchUpload() {
  const { t } = useTranslation();
  const errMsg = useErrorMessage();
  const [items, setItems] = useState<Item[]>([]);
  const api = productApi("business-cards");
  const update = (i: number, patch: Partial<Item>) => setItems((xs) => xs.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  const run = async (files: File[]) => {
    const start = items.length;
    setItems((xs) => [...xs, ...files.map((f) => ({ name: f.name, status: "draft" }))]);
    for (let k = 0; k < files.length; k++) {
      const i = start + k;
      try {
        const doc = await api.create({ title: files[k].name.replace(/\.[^.]+$/, ""), client_ref: uuid() });
        update(i, { id: doc.id, status: "ready" });
        await api.upload(doc.id, "front", files[k], (pct) => update(i, { pct }));
        const job = await api.process(doc.id, {});
        update(i, { status: job.status === "completed" ? "completed" : "queued", pct: undefined });
      } catch (e) {
        update(i, { status: "failed", error: errMsg(e) });
      }
    }
  };
  return (
    <Card className="flex flex-col gap-3 p-4">
      <h2 className="flex items-center gap-2 font-semibold"><Layers className="size-4" aria-hidden />{t("card.batch")}</h2>
      <p className="text-sm text-ink-2">{t("card.batchHint")}</p>
      <Dropzone multiple onFiles={run} />
      {items.length > 0 && (
        <ul className="flex flex-col gap-1 text-sm">
          {items.map((it, i) => (
            <li key={i} className="flex items-center gap-2 rounded-md border border-line px-2 py-1.5">
              <span className="min-w-0 flex-1 truncate" dir="auto">{it.name}</span>
              {it.pct !== undefined && <span className="text-xs text-ink-3">{t("upload.uploading", { pct: it.pct })}</span>}
              <StatusBadge status={it.status} />
              {it.id && <Link className="text-xs text-accent-ink underline" to={`/documents/${it.id}`}>{t("common.open")}</Link>}
              {it.error && <span className="text-xs text-red-600">{it.error}</span>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
