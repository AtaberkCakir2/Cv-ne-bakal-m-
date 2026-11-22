// Tanıtım sayfasının ekran görüntülerini (img/*.png) E2E ortamındaki web arayüzünden üretir (T-070).
// Sahte kullanıcı ve sahte CV kullanılır (CLAUDE.md kural 4); iş bitince hesap silinir.
//
//   bash tests/e2e/ortam.sh up
//   (cd web && VITE_API_URL=http://127.0.0.1:8000 npm run build && npx vite preview --host 127.0.0.1 --port 5173)
//   node infra/landing/ekran-goruntuleri.mjs
//   bash tests/e2e/ortam.sh down
//
// Playwright tests/e2e'den gelir (cd tests/e2e && npm ci && npx playwright install chromium).
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(new URL("../../tests/e2e/package.json", import.meta.url));
const { chromium } = require("@playwright/test");

const WEB = "http://127.0.0.1:5173";
const IMG = fileURLToPath(new URL("img/", import.meta.url));
const ORTAM = fileURLToPath(new URL("../../tests/e2e/ortam.sh", import.meta.url));
const EPOSTA = `tanitim-${Date.now()}@example.com`;
const SIFRE = "Tanitim-sahte-parola-123";

const sql = (sorgu) => execFileSync("bash", [ORTAM, "psql"], { input: sorgu, encoding: "utf-8" }).trim();

/** Tek sayfalık sahte CV (tests/e2e/yardimci/pdf.ts ile aynı yöntem). */
function sahteCvPdf() {
  const metin = ["Ornek Aday - Backend Gelistirici", "Yetkinlikler: Python, SQL, Git, REST API", "(sahte veri)"];
  const akis = ["BT", "/F1 12 Tf", "72 760 Td", "16 TL", ...metin.map((s) => `(${s}) Tj T*`), "ET"].join("\n");
  const nesneler = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    `<< /Length ${Buffer.byteLength(akis, "latin1")} >>\nstream\n${akis}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  let pdf = "%PDF-1.4\n";
  const konumlar = [];
  nesneler.forEach((govde, i) => {
    konumlar.push(Buffer.byteLength(pdf, "latin1"));
    pdf += `${i + 1} 0 obj\n${govde}\nendobj\n`;
  });
  const xref = Buffer.byteLength(pdf, "latin1");
  pdf += `xref\n0 ${nesneler.length + 1}\n0000000000 65535 f \n`;
  pdf += konumlar.map((k) => `${String(k).padStart(10, "0")} 00000 n \n`).join("");
  pdf += `trailer\n<< /Size ${nesneler.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(pdf, "latin1");
}

/**
 * Örnek analiz (ENVIRONMENT=test) eksik yetkinlikleri sözleşme örneğinden yazar ama örnekteki kaynak kimlikleri
 * veri tabanında yok; sonuç ekranında "kaynak yok" görünmesin diye her eksik yetkinliğe veri tabanındaki ilk canlı
 * kaynak öneri olarak eklenir (gerçek akıştaki biçimde, LLM gerekçesi yerine sabit metin).
 */
function onerileriDoldur(analizId) {
  if (!/^[0-9a-f-]{36}$/.test(analizId)) throw new Error(`Beklenmeyen analiz kimliği: ${analizId}`);
  sql(`
    INSERT INTO analysis_recommendations (analysis_id, skill_id, resource_id, rank, reason_text)
    SELECT '${analizId}', m.skill_id, r.id, 1,
           'Bu pozisyondaki ilanların çoğu bu yetkinliği istiyor; CV''nde bulunamadı. Türkçe, ücretsiz bir başlangıç kaynağı.'
    FROM analysis_skills m
    JOIN LATERAL (
      SELECT id FROM resources WHERE skill_id = m.skill_id AND is_alive ORDER BY language DESC, id LIMIT 1
    ) r ON true
    WHERE m.analysis_id = '${analizId}' AND m.kind = 'missing'
      AND NOT EXISTS (SELECT 1 FROM analysis_recommendations x WHERE x.analysis_id = m.analysis_id AND x.skill_id = m.skill_id);
  `);
}

/** Klavye odağı (sayfa geçişinde başlığa verilir) görüntüde çerçeve olarak çıkmasın. */
const odagiKaldir = (p) => p.evaluate(() => document.activeElement instanceof HTMLElement && document.activeElement.blur());

const tarayici = await chromium.launch();
try {
  const masaustu = await tarayici.newContext({ viewport: { width: 1280, height: 800 }, locale: "tr-TR", colorScheme: "light" });
  const page = await masaustu.newPage();

  await page.goto(`${WEB}/kayit`);
  await page.getByLabel("E-posta").fill(EPOSTA);
  await page.getByLabel("Şifre", { exact: true }).fill(SIFRE);
  await page.getByLabel("Şifre (tekrar)").fill(SIFRE);
  await page.getByLabel("KVKK aydınlatma metnini okudum.").check();
  await page.getByLabel(/açık rıza veriyorum/).check();
  await page.getByLabel("Kullanım koşullarını kabul ediyorum.").check();
  await page.getByRole("button", { name: "Kayıt ol" }).click();
  await page.getByRole("heading", { name: "E-postanı kontrol et" }).waitFor();

  await page.goto(`${WEB}/giris?sonra=/yukle`);
  await page.getByLabel("E-posta").fill(EPOSTA);
  await page.getByLabel("Şifre").fill(SIFRE);
  await page.getByRole("button", { name: "Giriş yap" }).click();
  await page.getByRole("heading", { name: "CV'ni yükle" }).waitFor();

  const pozisyon = page.getByLabel("Hedef pozisyon");
  await pozisyon.selectOption({ label: (await pozisyon.locator("option", { hasText: /Backend/ }).first().textContent()) ?? "" });
  await page.locator('input[type="file"]').setInputFiles({ name: "ornek-cv.pdf", mimeType: "application/pdf", buffer: sahteCvPdf() });
  await page.getByText("ornek-cv.pdf").waitFor();

  await page.getByRole("button", { name: "Analizi başlat" }).click();
  await page.waitForURL(/\/analiz\/[0-9a-f-]{36}$/);
  const analizId = page.url().split("/").pop();
  await page.getByRole("heading", { name: /CV'nde bulunanlar/ }).waitFor({ timeout: 90_000 });
  onerileriDoldur(analizId);
  await page.reload();
  await page.getByRole("heading", { name: "Eksiklerini kapatmak için kaynaklar" }).waitFor();
  await odagiKaldir(page);
  await page.screenshot({ path: `${IMG}sonuc.png`, fullPage: true, clip: { x: 0, y: 0, width: 1280, height: 1000 } });

  // Telefon görünümü (aynı oturum: çerezler/depolama yeni bağlama taşınır).
  const durum = await masaustu.storageState();
  const telefon = await tarayici.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, locale: "tr-TR", storageState: durum, colorScheme: "light" });
  const tp = await telefon.newPage();
  await tp.goto(page.url());
  await tp.getByRole("heading", { name: /Eksik yetkinlikler/ }).waitFor();
  await odagiKaldir(tp);
  await tp.screenshot({ path: `${IMG}telefon.png` });

  // Sahte hesabı sil. Telefon bağlamı oturumu yeniledi (refresh token dönüşümlü): masaüstündeki artık geçersiz.
  await tp.goto(`${WEB}/profil`);
  await tp.getByRole("button", { name: "Hesabımı sil" }).click();
  const pencere = tp.getByRole("dialog", { name: "Hesabın silinsin mi?" });
  await pencere.getByLabel("Şifre").fill(SIFRE);
  await pencere.getByRole("button", { name: "Hesabımı kalıcı olarak sil" }).click();
  await tp.waitForURL(/\/giris/);
  await telefon.close();
  console.log(`Ekran görüntüleri: ${IMG} (sonuc.png, telefon.png)`);
} finally {
  await tarayici.close();
}
