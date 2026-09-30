import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Languages, LogOut, Menu, Monitor, Moon, Sun, WifiOff } from "lucide-react";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { accountApi, auth } from "../lib/api";
import { useErrorMessage, useOnline } from "../lib/hooks";
import { useTheme, type ThemeMode } from "../lib/theme";
import { SUPPORTED_LANGS } from "../i18n";
import { Alert, Button, Card, Spinner, cx } from "./primitives";

export interface ProductBrand {
  key: "card";
  logo: ReactNode;
}

export function LanguageSelector({ compact }: { compact?: boolean }) {
  const { t, i18n } = useTranslation();
  return (
    <label className="inline-flex items-center gap-1.5 text-sm text-ink-2">
      <Languages className="size-4" aria-hidden />
      <span className={compact ? "sr-only" : ""}>{t("common.language")}</span>
      <select
        aria-label={t("common.language")}
        value={i18n.language}
        onChange={(e) => {
          i18n.changeLanguage(e.target.value);
          if (auth.token) accountApi.updateMe({ locale: e.target.value as "en" | "fr" | "ar" }).catch(() => undefined);
        }}
        className="rounded-md border border-line bg-surface px-2 py-1 text-sm text-ink"
      >
        {SUPPORTED_LANGS.map((l) => <option key={l} value={l}>{t(`lang.${l}`)}</option>)}
      </select>
    </label>
  );
}

export function ThemeToggle() {
  const { t } = useTranslation();
  const { mode, setMode } = useTheme();
  const opts: { v: ThemeMode; icon: ReactNode }[] = [
    { v: "light", icon: <Sun className="size-4" /> },
    { v: "dark", icon: <Moon className="size-4" /> },
    { v: "system", icon: <Monitor className="size-4" /> },
  ];
  return (
    <div role="radiogroup" aria-label={t("common.theme")} className="inline-flex rounded-lg border border-line bg-surface p-0.5">
      {opts.map((o) => (
        <button key={o.v} role="radio" aria-checked={mode === o.v} title={t(`common.${o.v}`)} onClick={() => setMode(o.v)}
          className={cx("rounded-md p-1.5 text-ink-2", mode === o.v && "bg-accent-soft text-accent-ink")}>
          {o.icon}<span className="sr-only">{t(`common.${o.v}`)}</span>
        </button>
      ))}
    </div>
  );
}

export function AppShell({ brand, children }: { brand: ProductBrand; children: ReactNode }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const online = useOnline();
  const qc = useQueryClient();
  const links = [
    { to: "/", label: t("nav.dashboard"), end: true },
    { to: "/new", label: t("nav.new") },
    { to: "/history", label: t("nav.history") },
    { to: "/settings", label: t("nav.settings") },
  ];
  return (
    <div className="min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:start-2 focus:top-2 focus:z-50 focus:rounded focus:bg-surface focus:p-2">{t("nav.skip")}</a>
      <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
          <NavLink to="/" className="flex items-center gap-2 font-semibold text-ink">
            {brand.logo}
            <span className="hidden whitespace-nowrap lg:inline">{t(`app.${brand.key}.name`)}</span>
          </NavLink>
          <nav aria-label="main" className="hidden flex-1 items-center gap-1 md:flex">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => cx("whitespace-nowrap rounded-md px-3 py-1.5 text-sm", isActive ? "bg-accent-soft font-medium text-accent-ink" : "text-ink-2 hover:bg-surface-2")}>
                {l.label}
              </NavLink>
            ))}
          </nav>
          <div className="ms-auto hidden items-center gap-3 md:flex">
            <LanguageSelector compact />
            <ThemeToggle />
            <Button variant="ghost" size="sm" onClick={async () => { await accountApi.logout(); qc.clear(); }}><LogOut className="size-4 rtl:-scale-x-100" aria-hidden />{t("nav.logout")}</Button>
          </div>
          <button className="ms-auto rounded-md p-2 md:hidden" aria-expanded={open} aria-controls="mobile-nav" aria-label={t("nav.menu")} onClick={() => setOpen((v) => !v)}><Menu className="size-5" /></button>
        </div>
        {open && (
          <nav id="mobile-nav" aria-label="mobile" className="border-t border-line px-4 py-3 md:hidden">
            <div className="flex flex-col gap-1">
              {links.map((l) => (
                <NavLink key={l.to} to={l.to} end={l.end} onClick={() => setOpen(false)} className={({ isActive }) => cx("rounded-md px-3 py-2 text-sm", isActive ? "bg-accent-soft text-accent-ink" : "text-ink-2")}>{l.label}</NavLink>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <LanguageSelector />
              <ThemeToggle />
              <Button variant="ghost" size="sm" onClick={async () => { await accountApi.logout(); qc.clear(); }}>{t("nav.logout")}</Button>
            </div>
          </nav>
        )}
      </header>
      {!online && (
        <div className="bg-amber-100 px-4 py-2 text-center text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200"><WifiOff className="me-1 inline size-4" />{t("errors.network_error")}</div>
      )}
      <main id="main" className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}

/** Shows the sign-in / sign-up screen until a session exists. */
export function AuthGate({ brand, children }: { brand: ProductBrand; children: ReactNode }) {
  const [authed, setAuthed] = useState<boolean | null>(auth.token ? true : null);
  const { i18n } = useTranslation();
  useEffect(() => {
    const unsub = auth.subscribe((a) => setAuthed(a));
    if (authed === null) {
      if (auth.hasSession()) auth.refresh().then((ok) => setAuthed(ok));
      else setAuthed(false);
    }
    return () => { unsub(); };
  }, [authed]);
  const me = useQuery({ queryKey: ["me"], queryFn: accountApi.me, enabled: authed === true });
  useEffect(() => {
    if (me.data?.locale && me.data.locale !== i18n.language && !localStorage.getItem("ocr.lang")) i18n.changeLanguage(me.data.locale);
  }, [me.data, i18n]);
  if (authed === null) return <div className="grid min-h-dvh place-items-center"><Spinner /></div>;
  if (!authed) return <LoginScreen brand={brand} />;
  return <>{children}</>;
}

export function LoginScreen({ brand }: { brand: ProductBrand }) {
  const { t, i18n } = useTranslation();
  const errMsg = useErrorMessage();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "signin") await accountApi.login(email, password);
      else await accountApi.register(email, password, name, i18n.language);
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="grid min-h-dvh place-items-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <div className="scale-150">{brand.logo}</div>
          <h1 className="mt-3 text-2xl font-semibold">{t(`app.${brand.key}.name`)}</h1>
          <p className="text-sm text-ink-2">{t(`app.${brand.key}.tagline`)}</p>
        </div>
        <Card className="p-6">
          <h2 className="mb-4 text-lg font-semibold">{mode === "signin" ? t("auth.welcome") : t("auth.create")}</h2>
          <form onSubmit={submit} className="flex flex-col gap-3" noValidate>
            {mode === "signup" && (
              <label className="flex flex-col gap-1 text-sm">{t("auth.name")}
                <input className="input" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
              </label>
            )}
            <label className="flex flex-col gap-1 text-sm">{t("auth.email")}
              <input className="input" type="email" dir="ltr" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
            </label>
            <label className="flex flex-col gap-1 text-sm">{t("auth.password")}
              <input className="input" type="password" dir="ltr" required minLength={mode === "signup" ? 10 : undefined} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "signin" ? "current-password" : "new-password"} aria-describedby={mode === "signup" ? "pw-hint" : undefined} />
              {mode === "signup" && <span id="pw-hint" className="text-xs text-ink-3">{t("auth.passwordHint")}</span>}
            </label>
            {error && <Alert tone="danger">{error}</Alert>}
            <Button type="submit" variant="primary" loading={busy}>{mode === "signin" ? t("auth.signin") : t("auth.signup")}</Button>
          </form>
          <p className="mt-4 text-center text-sm text-ink-2">
            {mode === "signin" ? t("auth.noAccount") : t("auth.haveAccount")}{" "}
            <button className="font-medium text-accent-ink underline" onClick={() => { setMode(mode === "signin" ? "signup" : "signin"); setError(null); }}>
              {mode === "signin" ? t("auth.signup") : t("auth.signin")}
            </button>
          </p>
        </Card>
        <div className="mt-4 flex items-center justify-center gap-3"><LanguageSelector /><ThemeToggle /></div>
      </div>
    </div>
  );
}
