import { defineConfig, devices } from "@playwright/test";

// Uçtan uca testler (T-071). Yığın (api, analiz işçisi, veritabanı) önceden `bash tests/e2e/ortam.sh up` ile kurulur;
// web arayüzü burada derlenip `vite preview` ile açılır. 5173: backend'in varsayılan CORS listesindeki adres.
const WEB_URL = "http://127.0.0.1:5173";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL: WEB_URL,
    locale: "tr-TR",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run build && npx vite preview --host 127.0.0.1 --port 5173 --strictPort",
    cwd: "../../web",
    url: WEB_URL,
    env: { VITE_API_URL: "http://127.0.0.1:8000" },
    timeout: 180_000,
    reuseExistingServer: !process.env.CI,
  },
});
