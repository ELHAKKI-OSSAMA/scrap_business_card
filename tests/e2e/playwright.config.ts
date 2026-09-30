import { defineConfig } from "@playwright/test";

/**
 * End-to-end tests against a running stack (real API + real OCR models).
 *   Local dev:  API on :8000, business-card-web on :5174
 *   Docker:     E2E_CARD_URL=http://localhost:8080/cards
 */
export default defineConfig({
  testDir: ".",
  timeout: 180_000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "../../test-results/e2e-report" }]],
  use: {
    channel: process.env.E2E_BROWSER_CHANNEL ?? "chrome",
    headless: true,
    locale: "en-GB",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  outputDir: "../../test-results/e2e",
});
