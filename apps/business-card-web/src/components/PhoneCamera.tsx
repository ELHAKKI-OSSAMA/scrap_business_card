import { Camera, Smartphone } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Button, Card, captureApi, productApi, useErrorMessage, type CaptureRequest } from "@ocr/ui";

/**
 * Phone side of "phone as camera": on the PC, New card → "Phone camera" creates a capture
 * request; this page (opened on the phone, same account) polls for it, takes the photo and
 * uploads it straight into the PC's card. Plain polling — works on Vercel serverless.
 */
export function PhoneCameraPage() {
  const { t } = useTranslation();
  const errMsg = useErrorMessage();
  const input = useRef<HTMLInputElement>(null);
  const [req, setReq] = useState<CaptureRequest | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;
    const tick = async () => { try { const r = await captureApi.pending(); if (!stop) setReq(r); } catch { /* offline: retry */ } };
    void tick();
    const h = window.setInterval(() => { if (!document.hidden) void tick(); }, 2500);
    return () => { stop = true; window.clearInterval(h); };
  }, []);

  const answer = async (f: File) => {
    if (!req) return;
    setBusy(true);
    setError(null);
    try {
      await productApi(req.route).upload(req.document_id, req.side, f);
      await captureApi.finish(req.id, "done");
      setReq(null);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4">
      <h1 className="text-2xl font-semibold">{t("phone.title")}</h1>
      <input ref={input} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) void answer(f); }} />
      {req ? (
        <Card className="flex flex-col gap-3 border-2 border-accent p-4">
          <p className="font-semibold">{t("upload.pcAsks", { side: t(`upload.${req.side}`) })}</p>
          <Button onClick={() => input.current?.click()} disabled={busy}><Camera className="size-4" aria-hidden />{busy ? t("phone.sending") : t("upload.shootForPc")}</Button>
          {error && <Alert tone="danger">{error}</Alert>}
          <Button variant="ghost" onClick={() => { void captureApi.finish(req.id, "cancel").catch(() => {}); setReq(null); }}>{t("common.cancel")}</Button>
        </Card>
      ) : (
        <Card className="flex flex-col items-center gap-3 p-6 text-center">
          <Smartphone className="size-10 animate-pulse text-accent-ink" aria-hidden />
          <p className="font-medium">{t("phone.waitingPc")}</p>
          <p className="text-sm text-ink-2">{t("phone.waitingPcHint")}</p>
        </Card>
      )}
    </div>
  );
}
