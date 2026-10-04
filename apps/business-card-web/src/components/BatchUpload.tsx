import { Layers } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Alert, Card, Dropzone, StatusBadge, captureApi, productApi, useErrorMessage, uuid } from "@ocr/ui";

type Item = { name: string; id?: string; status: string; error?: string; pct?: number };

/** Several single-sided cards at once: one record per image, processed independently. */
export function BatchUpload() {
  const { t } = useTranslation();
  const errMsg = useErrorMessage();
  const [items, setItems] = useState<Item[]>([]);
  const api = productApi("business-cards");
  const update = (i: number, patch: Partial<Item>) => setItems((xs) => xs.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  const updateId = (id: string, patch: Partial<Item>) => setItems((xs) => xs.map((x) => (x.id === id ? { ...x, ...patch } : x)));

  // Background workers (non-sync deployments): refresh cards until their OCR finishes.
  const inFlight = items.filter((x) => x.id && ["queued", "running", "processing"].includes(x.status)).map((x) => x.id!).join(",");
  useEffect(() => {
    if (!inFlight) return;
    const h = window.setInterval(() => {
      for (const id of inFlight.split(",")) void api.get(id).then((d) => updateId(id, { status: d.status }), () => {});
    }, 3000);
    return () => window.clearInterval(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inFlight]);

  // Phone mode: one capture request after another until stopped; each photo becomes a card.
  const [phone, setPhone] = useState<{ docId: string; reqId: string } | null>(null);
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const shots = useRef(0);
  const askNext = async () => {
    const doc = await api.create({ client_ref: uuid() });
    const r = await captureApi.create(doc.id, "front");
    setPhone({ docId: doc.id, reqId: r.id });
  };
  const startPhone = async () => {
    setPhoneError(null);
    try { await askNext(); } catch (e) { setPhoneError(errMsg(e)); }
  };
  const stopPhone = async () => {
    const cur = phone;
    setPhone(null);
    if (!cur) return;
    await captureApi.finish(cur.reqId, "cancel").catch(() => {});
    await api.remove(cur.docId).catch(() => {}); // the empty record waiting for a photo
  };
  useEffect(() => {
    if (!phone) return;
    const h = window.setInterval(async () => {
      try {
        const r = await captureApi.get(phone.reqId);
        if (r.status === "pending") return;
        window.clearInterval(h);
        if (r.status !== "done") { setPhone(null); return; }
        shots.current += 1;
        const id = phone.docId;
        setItems((xs) => [...xs, { name: t("phone.cardN", { n: shots.current }), id, status: "queued" }]);
        void api.process(id, {}).then(
          (j) => updateId(id, { status: j.status === "completed" ? "completed" : j.status }),
          (e) => updateId(id, { status: "failed", error: errMsg(e) }),
        );
        await askNext();
      } catch (e) {
        window.clearInterval(h);
        setPhoneError(errMsg(e));
        setPhone(null);
      }
    }, 2000);
    return () => window.clearInterval(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phone?.reqId]);

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
      <Dropzone multiple onFiles={run} onPhone={startPhone} phoneWaiting={!!phone} onCancelPhone={stopPhone}
        phoneWaitingText={t("card.batchPhoneWaiting", { n: shots.current })} cancelText={t("card.batchPhoneStop")} />
      {phoneError && <Alert tone="danger">{phoneError}</Alert>}
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
