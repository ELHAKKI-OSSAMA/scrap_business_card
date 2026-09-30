import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import { beforeAll, describe, expect, it, vi } from "vitest";
import type { BusinessCardData, DocumentOut, FieldValue } from "@ocr/shared-types";
import { ToastProvider, i18n, initI18n } from "@ocr/ui";
import { CardFields } from "./components/CardFields";

beforeAll(() => { initI18n("en"); });

const fv = (value: string | null): FieldValue<string> => ({ value, original_value: value, normalized_value: null, confidence: value ? 0.9 : null, source_region_ids: value ? ["f-0"] : [], extraction_method: "rule", review_status: "unreviewed", notes: null });

const base: BusinessCardData = {
  schema_version: "1.0", language_regions: [], languages: ["fr"], warnings: [], extractor: "rules", extractor_version: "1", generated_at: null,
  full_name: fv(null), first_name: fv(null), last_name: fv(null), arabic_name: fv(null), job_title: fv(null), company: fv(null), department: fv(null),
  industry: fv(null), specialty: fv(null), website: fv(null), linkedin: fv(null), address: null,
  phones: [{ type: "unknown", type_evidence: null, original: "06 12 34 56 78", e164: null, region: null, region_inferred_from: "none", is_valid: false, confidence: 0.6, source_region_ids: ["f-3"], review_status: "needs_review" }],
  emails: [fv("k@example.com")], social_profiles: [], qualifications: [], certifications: [], memberships: [], logo: null,
  qr_codes: [
    { id: "f-qr0", side: "front", raw: "BEGIN:VCARD\nFN:Karim Bennani\nTEL:+212612345678\nEMAIL:k@example.com\nEND:VCARD", kind: "vcard", parsed: { fn: ["Karim Bennani"], tel: ["+212612345678"], email: ["k@example.com"] }, url_is_safe: null, bbox: null, imported: false },
    { id: "f-qr1", side: "front", raw: "javascript:alert(1)", kind: "url", parsed: {}, url_is_safe: false, bbox: null, imported: false },
    { id: "f-qr2", side: "back", raw: "https://example.com/profile", kind: "url", parsed: {}, url_is_safe: true, bbox: null, imported: false },
  ],
};

function setup(data = base) {
  const patch = vi.fn().mockResolvedValue(undefined);
  const actions = { patch, onSet: (path: string, value: unknown) => patch([{ path, value }]), onVerify: vi.fn(), onLocate: vi.fn() };
  render(
    <QueryClientProvider client={new QueryClient()}>
      <I18nextProvider i18n={i18n}>
        <ToastProvider><CardFields doc={{ id: "c1" } as unknown as DocumentOut<BusinessCardData>} data={data} actions={actions} selected={[]} /></ToastProvider>
      </I18nextProvider>
    </QueryClientProvider>,
  );
  return patch;
}

describe("CardFields", () => {
  it("keeps the printed phone number and does not invent a country", () => {
    setup();
    expect(screen.getByText("06 12 34 56 78")).toBeInTheDocument();
    expect((screen.getByPlaceholderText("Country not determined") as HTMLInputElement).value).toBe("");
  });

  it("changes the phone type only when the user picks it", async () => {
    const patch = setup();
    expect(patch).not.toHaveBeenCalled();
    await userEvent.selectOptions(screen.getAllByLabelText("Phone numbers")[0], "mobile");
    expect(patch).toHaveBeenCalledWith([{ path: "phones.0.type", value: "mobile" }]);
  });

  it("never imports QR data automatically; import is an explicit action", async () => {
    const patch = setup();
    expect(patch).not.toHaveBeenCalled();
    await userEvent.click(screen.getAllByRole("button", { name: "Import into contact" })[0]);
    await waitFor(() => expect(patch).toHaveBeenCalledTimes(1));
    const changes = patch.mock.calls[0][0];
    expect(changes).toContainEqual({ path: "full_name", value: "Karim Bennani" });
    expect(changes).toContainEqual({ path: "phones", op: "append", value: { original: "+212612345678" } });
    expect(changes.some((c: { path: string }) => c.path === "emails")).toBe(false); // already present, not duplicated
    expect(changes).toContainEqual({ path: "qr_codes.0.imported", value: true });
  });

  it("shows unsafe QR URLs as inert text and safe ones as a link that opens only on click", () => {
    setup();
    expect(screen.getByText("javascript:alert(1)").tagName).toBe("PRE");
    expect(screen.queryByRole("link", { name: /javascript/ })).toBeNull();
    expect(screen.getByText("Not a safe web link — shown as text only.")).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /example\.com\/profile/ });
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("adds an e-mail through the append operation", async () => {
    const patch = setup();
    await userEvent.type(screen.getByLabelText("Add e-mail"), "new@example.com");
    await userEvent.click(screen.getAllByRole("button", { name: "Add" })[1]);
    await waitFor(() => expect(patch).toHaveBeenCalledWith([{ path: "emails", op: "append", value: "new@example.com" }]));
  });

  it("shows QR vs printed values side by side and changes nothing by itself", () => {
    const patch = setup({
      ...base,
      full_name: fv("Karim BENNANI"),
      qr_checks: [
        { field: "full_name", qr_id: "f-qr0", qr_value: "Karim Bennani", ocr_value: "Karim BENNANI", status: "match" },
        { field: "phones", qr_id: "f-qr0", qr_value: "+212612345678", ocr_value: null, status: "qr_only" },
        { field: "company", qr_id: "f-qr0", qr_value: "Other SARL", ocr_value: "Atlas SARL", status: "conflict" },
      ],
    });
    const table = screen.getByTestId("qr-comparison");
    expect(table).toHaveTextContent("Other SARL");
    expect(table).toHaveTextContent("Atlas SARL");
    expect(table).toHaveTextContent("Different — review");
    expect(table).toHaveTextContent("Only in QR code");
    expect(screen.getByText(/Nothing was changed automatically/)).toBeInTheDocument();
    expect(patch).not.toHaveBeenCalled();
  });

  it("shows normalized value, source region and an inferred-title note", () => {
    setup({
      ...base,
      specialty: { ...fv("HÉPATO-GASTROENTÉROLOGIE"), normalized_value: "hepato-gastroenterology", source_region_ids: ["f-0"], notes: "explicit specialty term printed on the card" },
      job_title: { ...fv("Médecin"), original_value: null, review_status: "needs_review", notes: "inferred: honorific 'Dr' + printed medical specialty; not printed as a title" },
      professional_description: fv("Spécialiste des maladies du foie et de l’appareil digestif"),
    });
    expect(screen.getByText("hepato-gastroenterology")).toBeInTheDocument();
    expect(screen.getAllByText(/f-0/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Inferred from “Dr”/)).toBeInTheDocument();
    expect(screen.getByText("Spécialiste des maladies du foie et de l’appareil digestif")).toBeInTheDocument();
  });
});
