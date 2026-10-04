import { Camera, Check, Monitor, RotateCcw, Smartphone } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import type { DocumentSummary } from "@ocr/shared-types";
import { Alert, Bidi, Button, Card, StatusBadge, cx, productApi, useErrorMessage, uuid } from "@ocr/ui";

const api = productApi("business-cards");
const isPhone = () => typeof window !== "undefined" && window.matchMedia("(pointer: coarse)").matches && window.innerWidth < 900;

/**
 * "Phone as camera": the same account is open on a phone and a PC. The phone side shoots
 * card after card (front, optional back) and sends each one without waiting for OCR; the PC
 * side polls the history and shows every new card as it arrives, optionally opening it.
 * Plain polling — no websocket — so it works on Vercel serverless.
 */
export function PhoneCameraPage() {
  const { t } = useTranslation();
  const [mode, setMode] = useState<"send" | "receive">(isPhone() ? "send" : "receive");
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <h1 className="text-2xl font-semibold">{t("phone.title")}</h1>
      <div role="tablist" className="inline-flex self-start rounded-lg border border-line bg-surface p-0.5">
        {([["send", Smartphone], ["receive", Monitor]] as const).map(([m, Icon]) => (
          <button key={m} role="tab" aria-selected={mode === m} onClick={() => setMode(m)}
            className={cx("inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm", mode === m ? "bg-accent text-accent-fg" : "text-ink-2")}>
            <Icon className="size-4" aria-hidden />{t(`phone.${m}Tab`)}
          </button>
        ))}
      </div>
      {mode === "send" ? <Sender /> : <Receiver />}
    </div>
  );
}

type Sent = { key: string; name: string; status: "sending" | "processing" | "completed" | "failed"; id?: string; error?: string };

function Sender() {
  const { t } = useTranslation();
  const errMsg = useErrorMessage();
  const front = useRef<HTMLInputElement>(null);
  const back = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState<File | null>(null);
  const [sent, setSent] = useState<Sent[]>([]);
  const upd = (key: string, p: Partial<Sent>) => setSent((xs) => xs.map((x) => (x.key === key ? { ...x, ...p } : x)));

  // Runs in the background so the user can shoot the next card straight away.
  const send = async (f: File, b: File | null) => {
    setPending(null);
    const key = uuid();
    const name = t("phone.cardN", { n: sent.length + 1 });
    setSent((xs) => [{ key, name, status: "sending" }, ...xs]);
    try {
      const doc = await api.create({ client_ref: key });
      upd(key, { id: doc.id });
      await api.upload(doc.id, "front", f);
      if (b) await api.upload(doc.id, "back", b);
      upd(key, { status: "processing" });
      const r = await api.process(doc.id, {});
      upd(key, { status: r.status === "failed" ? "failed" : "completed" });
    } catch (e) {
      upd(key, { status: "failed", error: errMsg(e) });
    }
  };

  return (
    <>
      <p className="text-sm text-ink-2">{t("phone.sendHint")}</p>
      <input ref={front} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden
        onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ""; if (f) setPending(f); }} />
      <input ref={back} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden
        onChange={(e) => { const b = e.target.files?.[0]; e.target.value = ""; if (b && pending) void send(pending, b); }} />
      {!pending ? (
        <button onClick={() => front.current?.click()}
          className="flex h-44 flex-col items-center justify-center gap-2 rounded-2xl bg-accent text-lg font-semibold text-accent-fg shadow-sm active:scale-[0.99]">
          <Camera className="size-10" aria-hidden />{t("phone.shootFront")}
        </button>
      ) : (
        <Card className="flex flex-col gap-3 p-4">
          <p className="flex items-center gap-2 font-medium"><Check className="size-5 text-green-600" aria-hidden />{t("phone.frontReady")}</p>
          <Button onClick={() => void send(pending, null)}>{t("phone.sendNow")}</Button>
          <Button variant="secondary" onClick={() => back.current?.click()}><Camera className="size-4" aria-hidden />{t("phone.addBack")}</Button>
          <Button variant="ghost" onClick={() => setPending(null)}><RotateCcw className="size-4" aria-hidden />{t("phone.retake")}</Button>
        </Card>
      )}
      {sent.length > 0 && (
        <Card className="p-3">
          <ul className="flex flex-col gap-1 text-sm">
            {sent.map((s) => (
              <li key={s.key} className="flex items-center gap-2 rounded-md px-2 py-1.5">
                <span className="flex-1">{s.name}</span>
                {s.error && <span className="text-xs text-red-600">{s.error}</span>}
                <StatusBadge status={s.status === "sending" ? "queued" : s.status} />
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  );
}

function Receiver() {
  const { t } = useTranslation();
  const nav = useNavigate();
  const known = useRef<Set<string> | null>(null);
  const [arrived, setArrived] = useState<DocumentSummary[]>([]);
  const [autoOpen, setAutoOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const errMsg = useErrorMessage();
  const autoOpenRef = useRef(autoOpen);
  autoOpenRef.current = autoOpen;
  const pendingIds = useRef(new Set<string>()); // arrived but not yet processed

  useEffect(() => {
    let stop = false;
    const tick = async () => {
      try {
        const page = await api.list({ sort: "created_desc", page_size: 20 });
        setError(null);
        if (known.current === null) { known.current = new Set(page.items.map((d) => d.id)); return; }
        const fresh = page.items.filter((d) => !known.current!.has(d.id));
        fresh.forEach((d) => known.current!.add(d.id));
        // refresh statuses of cards already listed, prepend new ones
        setArrived((xs) => [...fresh, ...xs.map((x) => page.items.find((d) => d.id === x.id) ?? x)]);
        fresh.forEach((d) => pendingIds.current.add(d.id));
        const done = page.items.find((d) => d.status === "completed" && pendingIds.current.has(d.id));
        if (done) {
          pendingIds.current.delete(done.id);
          if (autoOpenRef.current) nav(`/documents/${done.id}`);
        }
      } catch (e) {
        if (!stop) setError(errMsg(e));
      }
    };
    void tick();
    const h = window.setInterval(() => { if (!document.hidden) void tick(); }, 3000);
    return () => { stop = true; window.clearInterval(h); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <>
      <Card className="flex flex-col gap-2 p-4 text-sm">
        <p className="flex items-center gap-2 font-medium"><span className="relative flex size-2.5"><span className="absolute inline-flex size-full animate-ping rounded-full bg-green-500 opacity-60" /><span className="relative inline-flex size-2.5 rounded-full bg-green-500" /></span>{t("phone.listening")}</p>
        <p className="text-ink-2">{t("phone.receiveHint")}</p>
        <p dir="ltr" className="select-all rounded-md bg-surface-2 px-2 py-1 font-mono text-xs">{window.location.origin}/phone</p>
        <label className="mt-1 flex items-center gap-2"><input type="checkbox" checked={autoOpen} onChange={(e) => setAutoOpen(e.target.checked)} />{t("phone.autoOpen")}</label>
      </Card>
      {error && <Alert tone="danger">{error}</Alert>}
      {arrived.length === 0 ? <p className="text-center text-sm text-ink-3">{t("phone.waiting")}</p> : (
        <Card className="p-3">
          <ul className="flex flex-col gap-1 text-sm">
            {arrived.map((d) => (
              <li key={d.id} className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-surface-2">
                <Link to={`/documents/${d.id}`} className="min-w-0 flex-1 truncate font-medium"><Bidi>{d.summary.full_name || d.summary.company || t("phone.newCard")}</Bidi></Link>
                <StatusBadge status={d.status} />
              </li>
            ))}
          </ul>
        </Card>
      )}
    </>
  );
}
