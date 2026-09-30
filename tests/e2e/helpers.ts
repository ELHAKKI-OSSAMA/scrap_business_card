import { expect, type Page } from "@playwright/test";
import path from "node:path";

export const CARD_URL = process.env.E2E_CARD_URL ?? "http://localhost:5174";
export const SYNTH = path.resolve(__dirname, "../../ml/datasets/synthetic/out");

/** Test accounts are generated per run (throw-away addresses on example.com). */
export function newAccount(tag: string) {
  const id = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;
  return { email: `e2e-${tag}-${id}@example.com`, password: `e2e-${id}-${id}` };
}

export async function register(page: Page, baseUrl: string, acct: { email: string; password: string }) {
  await page.goto(baseUrl + "/");
  await page.getByRole("button", { name: "Create account" }).click();
  await page.getByLabel("Display name").fill("E2E");
  await page.getByLabel("E-mail").fill(acct.email);
  await page.getByLabel("Password").fill(acct.password);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("navigation", { name: "main" })).toBeVisible();
}

export async function uploadSide(page: Page, sideLabel: string, file: string) {
  const section = page.getByRole("region", { name: new RegExp(`^${sideLabel}`) });
  await section.locator('input[type=file]:not([capture])').setInputFiles(file);
  await expect(section.getByRole("img")).toBeVisible();
}
