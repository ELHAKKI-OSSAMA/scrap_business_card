import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { CARD_URL, SYNTH, newAccount, register, uploadSide } from "./helpers";

test("business card: mixed AR/FR photo → OCR → contact → correct → search → vCard → isolation", async ({ browser }) => {
  const ctxA = await browser.newContext({ locale: "en-GB" });
  const page = await ctxA.newPage();
  await register(page, CARD_URL, newAccount("bc"));

  await page.getByRole("link", { name: "New" }).first().click();
  await uploadSide(page, "Front", path.join(SYNTH, "bc-ar_fr-000-photo/front.jpg"));
  await page.getByRole("button", { name: "Run OCR" }).click();
  await page.waitForURL(/\/documents\//, { timeout: 120_000 });
  const docUrl = page.url();

  await expect(page.locator('[data-field="full_name"]')).toContainText("Youssef EL AMRANI");
  await expect(page.locator('[data-field="job_title"]')).toContainText("Avocat au Barreau de Rabat");
  await expect(page.locator('[data-field="company"]')).toContainText("Alaoui");
  await expect(page.getByText("+212 6 20 25 11 18", { exact: true })).toBeVisible();
  await expect(page.locator('[data-field="emails.0"]')).toContainText("@alaoui-avocats.ma");
  // Arabic line is kept verbatim and rendered with automatic direction
  const ar = page.locator('[data-field="arabic_name"] p[dir="rtl"]');
  await expect(ar).toBeVisible();

  // correct an uncertain field
  const title = page.locator('[data-field="department"]');
  await title.getByRole("button", { name: /^Edit/ }).click();
  await title.getByRole("textbox").fill("Faculté des Sciences");
  await title.getByRole("button", { name: "Save" }).click();
  await expect(title).toContainText("Corrected");

  // invalid e-mail: blocked by the browser's constraint validation…
  const addEmail = page.getByLabel("Add e-mail");
  await addEmail.fill("not-an-email");
  expect(await addEmail.evaluate((el: HTMLInputElement) => el.validity.valid)).toBe(false);
  // …and syntactically-HTML-valid but undeliverable addresses are rejected by the API, with a translated message
  await addEmail.fill("user@localhost");
  await addEmail.press("Enter");
  await expect(page.getByText("This e-mail address is not valid.").first()).toBeVisible();

  // search + vCard export
  await page.getByRole("link", { name: "History" }).first().click();
  await page.getByLabel("Search").fill("amrani");
  await expect(page.getByRole("link", { name: /Youssef EL AMRANI/ })).toBeVisible();
  await page.goto(docUrl);
  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "vCard (.vcf)" }).click();
  const vcf = fs.readFileSync((await (await dl).path())!, "utf-8");
  expect(vcf).toContain("BEGIN:VCARD");
  expect(vcf).toContain("FN:Youssef EL AMRANI");
  expect(vcf).toMatch(/TEL;TYPE=CELL:\+212620251118/);
  expect(vcf).toContain("Faculté des Sciences");

  // isolation
  const ctxB = await browser.newContext({ locale: "en-GB" });
  const pageB = await ctxB.newPage();
  await register(pageB, CARD_URL, newAccount("bc-other"));
  await pageB.goto(docUrl);
  await expect(pageB.getByText("Record not found.")).toBeVisible();
  await ctxA.close();
  await ctxB.close();
});
