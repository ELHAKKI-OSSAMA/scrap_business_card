import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { Badge, Bidi, Button, Card, ConfirmDialog, Spinner, productApi, useErrorMessage, useToast } from "@ocr/ui";

/** Duplicate suggestions. Merging always requires an explicit confirmation. */
export function Duplicates({ docId }: { docId: string }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const toast = useToast();
  const errMsg = useErrorMessage();
  const api = productApi("business-cards");
  const q = useQuery({ queryKey: ["business-cards", "dups", docId], queryFn: () => api.duplicates(docId) });
  const [target, setTarget] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  return (
    <Card className="flex flex-col gap-3 p-4">
      <h3 className="flex items-center gap-2 font-semibold"><Users className="size-4" aria-hidden />{t("card.duplicates")}</h3>
      {q.isLoading ? <Spinner /> : !q.data?.length ? <p className="text-sm text-ink-3">{t("card.noDuplicates")}</p> : (
        <ul className="flex flex-col gap-2">
          {q.data.map((d) => (
            <li key={d.document.id} className="flex flex-wrap items-center gap-2 rounded-lg border border-line p-2 text-sm">
              <Link to={`/documents/${d.document.id}`} className="font-medium text-accent-ink underline"><Bidi>{d.document.summary.full_name ?? d.document.title ?? "—"}</Bidi></Link>
              <span className="text-ink-3"><Bidi>{d.document.summary.company ?? ""}</Bidi></span>
              <span className="text-xs text-ink-3">{t("card.matched")}: {d.matched_keys.map((k) => <Badge key={k} className="me-1">{k.split(":")[0]}</Badge>)}</span>
              <Button size="sm" className="ms-auto" onClick={() => setTarget(d.document.id)}>{t("card.merge")}</Button>
            </li>
          ))}
        </ul>
      )}
      <ConfirmDialog open={!!target} title={t("card.merge")} body={t("card.mergeConfirm")} confirmLabel={t("common.confirm")} busy={busy}
        onCancel={() => setTarget(null)}
        onConfirm={async () => {
          setBusy(true);
          try {
            await api.merge(docId, target!);
            qc.invalidateQueries({ queryKey: ["business-cards"] });
            toast("success", t("fields.saved"));
          } catch (e) { toast("danger", errMsg(e)); }
          setBusy(false);
          setTarget(null);
        }} />
    </Card>
  );
}
