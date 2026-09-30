import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import { beforeAll, describe, expect, it, vi } from "vitest";
import type { FieldValue } from "@ocr/shared-types";
import { ConfidenceBadge, ReviewBadge } from "./components/primitives";
import { FieldRow } from "./components/review";
import { Dropzone } from "./components/upload";
import { i18n, initI18n } from "./i18n";
import en from "./i18n/locales/en.json";
import fr from "./i18n/locales/fr.json";
import ar from "./i18n/locales/ar.json";
import { safeHttpUrl, formatDate } from "./lib/format";
import { translateNote } from "./lib/notes";

beforeAll(() => { initI18n("en"); });

const wrap = (ui: React.ReactElement) => render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);

const field = (over: Partial<FieldValue<string>> = {}): FieldValue<string> => ({
  value: "Karim BENNANI", original_value: "Dr. Karim BENNANI", normalized_value: null, confidence: 0.58,
  source_region_ids: ["f-0"], extraction_method: "layout", review_status: "needs_review", notes: "honorific: Dr.", ...over,
});

describe("i18n catalogues", () => {
  const keys = (o: Record<string, unknown>, p = ""): string[] =>
    Object.entries(o).flatMap(([k, v]) => (v && typeof v === "object" ? keys(v as Record<string, unknown>, `${p}${k}.`) : [`${p}${k}`]));
  it("fr and ar define every English key (no hard-coded fallbacks)", () => {
    const base = new Set(keys(en));
    for (const cat of [fr, ar]) {
      const missing = [...base].filter((k) => !new Set(keys(cat)).has(k));
      expect(missing).toEqual([]);
    }
  });
  it("switching to Arabic sets RTL on <html>, and back to LTR", async () => {
    await i18n.changeLanguage("ar");
    expect(document.documentElement.dir).toBe("rtl");
    expect(document.documentElement.lang).toBe("ar");
    await i18n.changeLanguage("fr");
    expect(document.documentElement.dir).toBe("ltr");
    await i18n.changeLanguage("en");
  });
});

describe("badges", () => {
  it("shows a confidence percentage with a non-guarantee disclaimer", () => {
    wrap(<ConfidenceBadge value={0.93} />);
    const b = screen.getByText(/93/);
    expect(b.closest("span")?.getAttribute("title")).toMatch(/not a guarantee/);
  });
  it("says 'No estimate' instead of inventing a number", () => {
    wrap(<ConfidenceBadge value={null} />);
    expect(screen.getByText("No estimate")).toBeInTheDocument();
  });
  it("translates review status", async () => {
    await i18n.changeLanguage("fr");
    wrap(<ReviewBadge status="needs_review" />);
    expect(screen.getByText("À vérifier")).toBeInTheDocument();
    await i18n.changeLanguage("en");
  });
});

describe("FieldRow", () => {
  it("shows value, OCR evidence and method; highlights uncertain fields", () => {
    wrap(<FieldRow label="Full name" path="full_name" field={field()} actions={{ onSet: vi.fn(), onVerify: vi.fn(), onLocate: vi.fn() }} />);
    expect(screen.getByText("Karim BENNANI")).toBeInTheDocument();
    expect(screen.getByText("Dr. Karim BENNANI")).toBeInTheDocument();
    expect(screen.getByText("Layout")).toBeInTheDocument();
    expect(screen.getByText("Needs review")).toBeInTheDocument();
    expect(screen.getByText("Title printed before the name: Dr.")).toBeInTheDocument();
  });

  it("edits a value and calls onSet with the path", async () => {
    const onSet = vi.fn().mockResolvedValue(undefined);
    wrap(<FieldRow label="Full name" path="full_name" field={field()} actions={{ onSet, onVerify: vi.fn(), onLocate: vi.fn() }} />);
    await userEvent.click(screen.getByRole("button", { name: /Edit Full name/ }));
    const input = screen.getByRole("textbox");
    await userEvent.clear(input);
    await userEvent.type(input, "Karim Bennani{Enter}");
    await waitFor(() => expect(onSet).toHaveBeenCalledWith("full_name", "Karim Bennani"));
  });

  it("shows a translated validation error from the API and stays in edit mode", async () => {
    const { ApiError } = await import("./lib/api");
    const onSet = vi.fn().mockRejectedValue(new ApiError(422, "invalid_email", "bad"));
    wrap(<FieldRow label="E-mail" path="emails.0" field={field({ value: "a@b.c" })} actions={{ onSet, onVerify: vi.fn(), onLocate: vi.fn() }} />);
    await userEvent.click(screen.getByRole("button", { name: /Edit E-mail/ }));
    await userEvent.type(screen.getByRole("textbox"), "x{Enter}");
    expect(await screen.findByText("This e-mail address is not valid.")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("locate button reports the OCR source region ids", async () => {
    const onLocate = vi.fn();
    wrap(<FieldRow label="Full name" path="full_name" field={field()} actions={{ onSet: vi.fn(), onVerify: vi.fn(), onLocate }} />);
    await userEvent.click(screen.getByRole("button", { name: "Show source on image" }));
    expect(onLocate).toHaveBeenCalledWith(["f-0"]);
  });

  it("renders Arabic values with automatic direction", () => {
    wrap(<FieldRow label="Arabic name" path="arabic_name" field={field({ value: "كريم بناني", original_value: null })} actions={{ onSet: vi.fn(), onVerify: vi.fn(), onLocate: vi.fn() }} />);
    expect(screen.getByText("كريم بناني").getAttribute("dir")).toBe("auto");
  });
});

describe("Dropzone", () => {
  it("passes selected files to the handler", async () => {
    const onFiles = vi.fn();
    const { container } = wrap(<Dropzone onFiles={onFiles} />);
    const input = container.querySelector('input[type=file]:not([capture])') as HTMLInputElement;
    const file = new File([new Uint8Array([0xff, 0xd8, 0xff])], "card.jpg", { type: "image/jpeg" });
    await userEvent.upload(input, file);
    expect(onFiles).toHaveBeenCalledWith([file]);
  });
  it("offers camera capture", () => {
    const { container } = wrap(<Dropzone onFiles={vi.fn()} />);
    expect(container.querySelector('input[capture="environment"]')).not.toBeNull();
  });
});

describe("helpers", () => {
  it("only http(s) links are clickable", () => {
    expect(safeHttpUrl("https://example.com/a")).toBe("https://example.com/a");
    expect(safeHttpUrl("javascript:alert(1)")).toBeNull();
    expect(safeHttpUrl("https://user:pw@example.com")).toBeNull();
    expect(safeHttpUrl("data:text/html,x")).toBeNull();
  });
  it("Arabic dates use Latin digits", () => {
    expect(formatDate("2026-03-05T10:00:00Z", "ar")).toMatch(/2026/);
  });
  it("unknown notes are shown verbatim, never dropped", () => {
    expect(translateNote("something new", i18n.t)).toBe("something new");
  });
});
