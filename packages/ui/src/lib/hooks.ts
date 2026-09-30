import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { DocumentOut, Job } from "@ocr/shared-types";
import { accountApi, ApiError, productApi, type ProductRoute } from "./api";

export function useErrorMessage() {
  const { t } = useTranslation();
  return (e: unknown) => {
    if (e instanceof ApiError) {
      const key = `errors.${e.code}`;
      const msg = t(key);
      return msg === key ? e.message || t("errors.generic") : msg;
    }
    return t("errors.generic");
  };
}

export function useDocument<D>(route: ProductRoute, id: string | undefined) {
  return useQuery({
    queryKey: [route, "doc", id],
    queryFn: () => productApi(route).get<D>(id!),
    enabled: !!id,
    refetchInterval: (q) => {
      const s = (q.state.data as DocumentOut | undefined)?.status;
      return s === "queued" || s === "processing" ? 1500 : false;
    },
  });
}

export function useJob(jobId: string | null | undefined, onDone?: (job: Job) => void) {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => accountApi.job(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const s = (query.state.data as Job | undefined)?.status;
      return s === "completed" || s === "failed" ? false : 1200;
    },
  });
  const status = q.data?.status;
  useEffect(() => {
    if (q.data && (status === "completed" || status === "failed")) {
      qc.invalidateQueries();
      onDone?.(q.data);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);
  return q;
}

/** Fetches an authenticated image as a blob URL (images are never public). */
export function useAuthedImage(route: ProductRoute, path: string | null | undefined) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let revoked: string | null = null;
    let cancelled = false;
    setUrl(null);
    setError(false);
    if (!path) return;
    productApi(route).imageBlobUrl(path).then(
      (u) => { if (cancelled) URL.revokeObjectURL(u); else { revoked = u; setUrl(u); } },
      () => !cancelled && setError(true),
    );
    return () => { cancelled = true; if (revoked) URL.revokeObjectURL(revoked); };
  }, [route, path]);
  return { url, error };
}

export function useOnline() {
  const [online, setOnline] = useState(typeof navigator === "undefined" ? true : navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, []);
  return online;
}
