import type { ApiErrorBody, Duplicate, DocumentOut, DocumentSummary, FieldChange, Job, Me, PageOf, ReviewEvent, Side } from "@ocr/shared-types";
import { shrinkForUpload } from "./image";

/**
 * API client. The access token lives only in memory; the refresh token is kept in
 * localStorage so a reload keeps the session (trade-off documented in docs/security/privacy.md).
 * On 401 the client rotates the refresh token once and retries.
 */
export const API_BASE: string = (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE ?? "/api/v1";
const REFRESH_KEY = "ocr.refresh";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: Record<string, unknown> = {}) {
    super(message);
  }
}

let accessToken: string | null = null;
let refreshing: Promise<boolean> | null = null;
const listeners = new Set<(authed: boolean) => void>();

export const auth = {
  get token() { return accessToken; },
  hasSession() {
    try { return !!localStorage.getItem(REFRESH_KEY); } catch { return false; }
  },
  set(access: string, refresh: string) {
    accessToken = access;
    try { localStorage.setItem(REFRESH_KEY, refresh); } catch { /* private mode */ }
    listeners.forEach((l) => l(true));
  },
  clear() {
    accessToken = null;
    try { localStorage.removeItem(REFRESH_KEY); } catch { /* ignore */ }
    listeners.forEach((l) => l(false));
  },
  subscribe(fn: (authed: boolean) => void) { listeners.add(fn); return () => listeners.delete(fn); },
  async refresh(): Promise<boolean> {
    if (refreshing) return refreshing;
    const rt = (() => { try { return localStorage.getItem(REFRESH_KEY); } catch { return null; } })();
    if (!rt) return false;
    refreshing = (async () => {
      const r = await fetch(`${API_BASE}/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) });
      if (!r.ok) { auth.clear(); return false; }
      const t = await r.json();
      auth.set(t.access_token, t.refresh_token);
      return true;
    })().finally(() => { refreshing = null; });
    return refreshing;
  },
};

async function toError(r: Response): Promise<ApiError> {
  try {
    const body = (await r.json()) as ApiErrorBody;
    return new ApiError(r.status, body.error?.code ?? "http_error", body.error?.message ?? r.statusText, body.error?.details ?? {});
  } catch {
    return new ApiError(r.status, r.status === 0 ? "network_error" : "http_error", r.statusText);
  }
}

export async function request(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let r: Response;
  try {
    r = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "network_error", "Network error");
  }
  if (r.status === 401 && retry && (await auth.refresh())) return request(path, init, false);
  if (!r.ok) throw await toError(r);
  return r;
}

const json = async <T,>(path: string, init?: RequestInit) => (await request(path, init)).json() as Promise<T>;

export type ProductRoute = "business-cards";

export interface ListParams { q?: string; status?: string; review_status?: string; language?: string; page?: number; page_size?: number; sort?: string }

export function productApi(route: ProductRoute) {
  const base = `/${route}`;
  return {
    list: (p: ListParams = {}) => {
      const qs = new URLSearchParams(Object.entries(p).filter(([, v]) => v !== undefined && v !== "").map(([k, v]) => [k, String(v)]));
      return json<PageOf<DocumentSummary>>(`${base}?${qs}`);
    },
    get: <D,>(id: string) => json<DocumentOut<D>>(`${base}/${id}`),
    create: (body: { title?: string; notes?: string; client_ref?: string }) => json<DocumentOut>(base, { method: "POST", body: JSON.stringify(body) }),
    updateMeta: (id: string, body: { title?: string | null; notes?: string | null }) => json<DocumentOut>(`${base}/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    upload: async (id: string, side: Side, file: File, onProgress?: (pct: number) => void) => uploadWithProgress(`${base}/${id}/images?side=${side}`, await shrinkForUpload(file), onProgress),
    removeImage: (id: string, side: Side) => json<DocumentOut>(`${base}/${id}/images/${side}`, { method: "DELETE" }),
    process: (id: string, body: { languages?: string[] | null; force?: boolean; use_llm?: boolean }) => json<{ job_id: string; status: string; reused: boolean }>(`${base}/${id}/process`, { method: "POST", body: JSON.stringify(body) }),
    patchFields: (id: string, changes: FieldChange[], expected_version?: number) => json<DocumentOut>(`${base}/${id}/fields`, { method: "PATCH", body: JSON.stringify({ changes, expected_version }) }),
    review: (id: string, status: string, note?: string) => json<DocumentOut>(`${base}/${id}/review`, { method: "POST", body: JSON.stringify({ status, note }) }),
    history: (id: string) => json<ReviewEvent[]>(`${base}/${id}/history`),
    remove: (id: string) => request(`${base}/${id}`, { method: "DELETE" }),
    duplicates: (id: string) => json<Duplicate[]>(`${base}/${id}/duplicates`),
    merge: (id: string, other_id: string) => json<DocumentOut>(`${base}/${id}/merge`, { method: "POST", body: JSON.stringify({ other_id, confirm: true }) }),
    imageBlobUrl: async (path: string) => URL.createObjectURL(await (await request(path.replace(API_BASE, ""))).blob()),
    download: async (path: string, fallbackName: string) => {
      const r = await request(path);
      const cd = r.headers.get("Content-Disposition") ?? "";
      const name = /filename="([^"]+)"/.exec(cd)?.[1] ?? fallbackName;
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    },
  };
}

function uploadWithProgress(path: string, file: File, onProgress?: (pct: number) => void, retry = true): Promise<DocumentOut> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}${path}`);
    if (accessToken) xhr.setRequestHeader("Authorization", `Bearer ${accessToken}`);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100)); };
    xhr.onerror = () => reject(new ApiError(0, "network_error", "Network error"));
    xhr.onload = async () => {
      if (xhr.status === 401 && retry && (await auth.refresh())) {
        uploadWithProgress(path, file, onProgress, false).then(resolve, reject);
        return;
      }
      let body: unknown = null;
      try { body = JSON.parse(xhr.responseText); } catch { /* ignore */ }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as DocumentOut);
      else {
        const e = (body as ApiErrorBody | null)?.error;
        reject(new ApiError(xhr.status, e?.code ?? "http_error", e?.message ?? xhr.statusText, e?.details ?? {}));
      }
    };
    const fd = new FormData();
    fd.append("file", file);
    xhr.send(fd);
  });
}

export const accountApi = {
  login: async (email: string, password: string) => {
    const t = await json<{ access_token: string; refresh_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    auth.set(t.access_token, t.refresh_token);
  },
  register: async (email: string, password: string, display_name: string, locale: string) => {
    const t = await json<{ access_token: string; refresh_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password, display_name, locale }) });
    auth.set(t.access_token, t.refresh_token);
  },
  logout: async () => {
    const rt = (() => { try { return localStorage.getItem(REFRESH_KEY); } catch { return null; } })();
    if (rt) await fetch(`${API_BASE}/auth/logout`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) }).catch(() => undefined);
    auth.clear();
  },
  me: () => json<Me>("/me"),
  updateMe: (body: Partial<Pick<Me, "display_name" | "locale" | "default_phone_region">>) => json<Me>("/me", { method: "PATCH", body: JSON.stringify(body) }),
  job: (id: string) => json<Job>(`/jobs/${id}`),
  models: () => json<Record<string, unknown>>("/models"),
  translate: (text: string, target: string) => json<{ translated_text: string; machine_generated: boolean; provider: string }>("/translate", { method: "POST", body: JSON.stringify({ text, target, source: "auto" }) }),
};
