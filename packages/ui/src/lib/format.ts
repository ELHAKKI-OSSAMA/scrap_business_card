/** Locale-aware formatting. Arabic UI uses Latin digits (`-u-nu-latn`), the common convention
 * in the Maghreb and the safer choice next to phone numbers and postal codes. */
export function intlLocale(lang: string): string {
  return lang === "ar" ? "ar-u-nu-latn" : lang === "fr" ? "fr-FR" : "en-GB";
}

export function formatDateTime(iso: string | null | undefined, lang: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(intlLocale(lang), { dateStyle: "medium", timeStyle: "short" }).format(d);
}

export function formatDate(iso: string | null | undefined, lang: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat(intlLocale(lang), { dateStyle: "medium" }).format(d);
}

export function formatNumber(n: number | null | undefined, lang: string, opts?: Intl.NumberFormatOptions): string {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat(intlLocale(lang), opts).format(n);
}

export function formatPercent(n: number | null | undefined, lang: string): string {
  return formatNumber(n, lang, { style: "percent", maximumFractionDigits: 0 });
}

export function formatBytes(n: number, lang: string): string {
  const units = ["B", "KB", "MB"];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${formatNumber(v, lang, { maximumFractionDigits: 1 })} ${units[i]}`;
}

export function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID().replace(/-/g, "");
  return Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
}

/** Only http(s) links without credentials are ever rendered as clickable. */
export function safeHttpUrl(raw: string | null | undefined): string | null {
  if (!raw) return null;
  try {
    const u = new URL(raw);
    if ((u.protocol === "http:" || u.protocol === "https:") && !u.username && !u.password && u.hostname.includes(".")) return u.toString();
  } catch { /* not a URL */ }
  return null;
}
