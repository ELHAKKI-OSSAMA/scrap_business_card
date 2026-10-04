import { useTranslation } from "react-i18next";
import { Route, Routes } from "react-router-dom";
import type { BusinessCardData } from "@ocr/shared-types";
import { AppShell, AuthGate, Bidi, DashboardPage, DocumentListPage, DocumentWorkspace, NewDocumentPage, SettingsPage, type ProductBrand, type ProductUi } from "@ocr/ui";
import { BatchUpload } from "./components/BatchUpload";
import { CardFields } from "./components/CardFields";
import { Duplicates } from "./components/Duplicates";
import { PhoneCameraPage } from "./components/PhoneCamera";

function Logo() {
  return (
    <svg viewBox="0 0 32 32" className="size-7" aria-hidden>
      <rect x="2" y="7" width="28" height="18" rx="3" fill="var(--accent)" />
      <circle cx="10" cy="15" r="3.2" fill="var(--accent-fg)" />
      <path d="M5.5 21.5c1-2.2 2.6-3.2 4.5-3.2s3.5 1 4.5 3.2" fill="var(--accent-fg)" />
      <path d="M17 13h9M17 16.5h9M17 20h6" stroke="var(--accent-fg)" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export const brand: ProductBrand = { key: "card", logo: <Logo /> };

function useUi(): ProductUi {
  const { t } = useTranslation();
  return {
    route: "business-cards",
    i18nKey: "card",
    sides: [{ side: "front", optional: false }, { side: "back", optional: true }],
    exportFormats: ["vcf", "csv", "json"],
    docTitle: (doc) => {
      const d = doc.data as BusinessCardData | null;
      return (d?.full_name.value as string | null) ?? (d?.arabic_name.value as string | null) ?? null;
    },
    primaryText: (d) => <Bidi>{d.summary.full_name || d.title || t("common.unknown")}</Bidi>,
    columns: [
      { key: "company", label: t("card.fields.company"), render: (d) => <Bidi>{d.summary.company ?? "—"}</Bidi> },
      { key: "job", label: t("card.fields.job_title"), render: (d) => <Bidi>{d.summary.job_title ?? "—"}</Bidi> },
      { key: "email", label: t("card.fields.emails"), render: (d) => <span dir="ltr">{d.summary.email ?? "—"}</span> },
      { key: "phone", label: t("card.fields.phones"), render: (d) => <span dir="ltr">{d.summary.phone ?? "—"}</span> },
    ],
    regionLabel: (l) => t(`regions.${l}`, { defaultValue: l }),
  };
}

export default function App() {
  const ui = useUi();
  return (
    <AuthGate brand={brand}>
      <AppShell brand={brand}>
        <Routes>
          <Route path="/" element={<DashboardPage ui={ui} />} />
          <Route path="/new" element={<div className="flex flex-col gap-6"><NewDocumentPage ui={ui} /><div className="mx-auto w-full max-w-4xl"><BatchUpload /></div></div>} />
          <Route path="/history" element={<DocumentListPage ui={ui} />} />
          <Route path="/documents/:id" element={<DocumentWorkspace<BusinessCardData> ui={ui} renderFields={(p) => <CardFields {...p} />} renderAside={(p) => <Duplicates docId={p.doc.id} />} />} />
          <Route path="/phone" element={<PhoneCameraPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<DashboardPage ui={ui} />} />
        </Routes>
      </AppShell>
    </AuthGate>
  );
}
