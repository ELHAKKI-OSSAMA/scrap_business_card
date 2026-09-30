import { useEffect, useState } from "react";

export type ThemeMode = "light" | "dark" | "system";
const KEY = "ocr.theme";

function resolve(mode: ThemeMode): "light" | "dark" {
  if (mode !== "system") return mode;
  return typeof matchMedia !== "undefined" && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(mode: ThemeMode) {
  const el = document.documentElement;
  const r = resolve(mode);
  el.dataset.theme = r;
  el.classList.toggle("dark", r === "dark");
}

export function initialTheme(): ThemeMode {
  try {
    const v = localStorage.getItem(KEY);
    if (v === "light" || v === "dark" || v === "system") return v;
  } catch { /* ignore */ }
  return "system";
}

export function useTheme() {
  const [mode, setMode] = useState<ThemeMode>(initialTheme);
  useEffect(() => {
    applyTheme(mode);
    try { localStorage.setItem(KEY, mode); } catch { /* ignore */ }
    if (mode !== "system" || typeof matchMedia === "undefined") return;
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const on = () => applyTheme("system");
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [mode]);
  return { mode, setMode };
}
