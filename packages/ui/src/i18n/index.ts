import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./locales/ar.json";
import en from "./locales/en.json";
import fr from "./locales/fr.json";

export const SUPPORTED_LANGS = ["en", "fr", "ar"] as const;
export type UiLang = (typeof SUPPORTED_LANGS)[number];
const KEY = "ocr.lang";

const read = (): string | null => { try { return localStorage.getItem(KEY); } catch { return null; } };
const write = (v: string) => { try { localStorage.setItem(KEY, v); } catch { /* ignore */ } };

export function isRtl(lang: string) {
  return lang === "ar";
}

export function applyDirection(lang: string) {
  if (typeof document === "undefined") return;
  document.documentElement.lang = lang;
  document.documentElement.dir = isRtl(lang) ? "rtl" : "ltr";
}

export function detectInitialLanguage(): UiLang {
  const saved = read();
  if (saved && (SUPPORTED_LANGS as readonly string[]).includes(saved)) return saved as UiLang;
  const nav = typeof navigator !== "undefined" ? navigator.language.slice(0, 2) : "en";
  return ((SUPPORTED_LANGS as readonly string[]).includes(nav) ? nav : "en") as UiLang;
}

export function initI18n(lng: UiLang = detectInitialLanguage()) {
  if (!i18n.isInitialized) {
    i18n.use(initReactI18next).init({
      resources: { en: { translation: en }, fr: { translation: fr }, ar: { translation: ar } },
      lng,
      fallbackLng: "en",
      interpolation: { escapeValue: false }, // React escapes output
      returnNull: false,
    });
    i18n.on("languageChanged", (l) => { applyDirection(l); write(l); });
  }
  applyDirection(i18n.language);
  return i18n;
}

export { i18n };
