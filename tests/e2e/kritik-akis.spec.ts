import { expect, test } from "@playwright/test";

import { sahteCvPdf } from "./yardimci/pdf";
import { eksikYetkinlikVeKaynakEkle } from "./yardimci/veritabani";

// T-071 kabul kriteri: kayıt → CV yükle → sonuç → kaynak aç → hesap sil. Her çalıştırma yeni, sahte bir kullanıcıyla
// başlar ve sonunda o kullanıcıyı siler (e-posta @example.com: gerçek bir adrese e-posta gitmez).
const EPOSTA = `e2e-${Date.now()}@example.com`;
const SIFRE = "E2e-sahte-parola-123";

test.describe.configure({ mode: "serial" });

test("kayıt → CV yükle → sonuç → kaynak aç → hesap sil", async ({ page, context }) => {
  await test.step("kayıt", async () => {
    await page.goto("/kayit");
    await page.getByLabel("E-posta").fill(EPOSTA);
    await page.getByLabel("Şifre", { exact: true }).fill(SIFRE);
    await page.getByLabel("Şifre (tekrar)").fill(SIFRE);
    await page.getByLabel("KVKK aydınlatma metnini okudum.").check();
    await page.getByLabel(/açık rıza veriyorum/).check();
    await page.getByLabel("Kullanım koşullarını kabul ediyorum.").check();
    await page.getByRole("button", { name: "Kayıt ol" }).click();
    await expect(page.getByRole("heading", { name: "E-postanı kontrol et" })).toBeVisible();
  });

  await test.step("giriş", async () => {
    await page.goto("/giris?sonra=/yukle");
    await page.getByLabel("E-posta").fill(EPOSTA);
    await page.getByLabel("Şifre").fill(SIFRE);
    await page.getByRole("button", { name: "Giriş yap" }).click();
    await expect(page.getByRole("heading", { name: "CV'ni yükle" })).toBeVisible();
  });

  let analizId = "";
  await test.step("CV yükle", async () => {
    const pozisyon = page.getByLabel("Hedef pozisyon");
    await expect(pozisyon.locator("option")).not.toHaveCount(1); // "Seç…" dışında pozisyon var (seed-taxonomy)
    await pozisyon.selectOption({ index: 1 });
    await page.locator('input[type="file"]').setInputFiles({
      name: "ornek-cv.pdf",
      mimeType: "application/pdf",
      buffer: sahteCvPdf(),
    });
    await expect(page.getByText("ornek-cv.pdf")).toBeVisible();
    await page.getByRole("button", { name: "Analizi başlat" }).click();
    await page.waitForURL(/\/analiz\/[0-9a-f-]{36}$/);
    analizId = page.url().split("/").pop() ?? "";
  });

  await test.step("sonuç", async () => {
    // Bekleme ekranı 3 sn'de bir yoklar; örnek analiz birkaç saniyede biter.
    await expect(page.getByRole("heading", { name: /CV'nde bulunanlar/ })).toBeVisible({ timeout: 90_000 });
    await expect(page.getByRole("heading", { name: /Eksik yetkinlikler/ })).toBeVisible();
  });

  await test.step("kaynak aç", async () => {
    const { kaynakBasligi, kaynakUrl } = eksikYetkinlikVeKaynakEkle(analizId);
    await page.reload();
    await expect(page.getByRole("heading", { name: "Eksiklerini kapatmak için kaynaklar" })).toBeVisible();
    await page.getByRole("button", { name: new RegExp(escape(kaynakBasligi)) }).click();

    const pencere = page.getByRole("dialog", { name: kaynakBasligi });
    const git = pencere.getByRole("link", { name: /Kaynağa git/ });
    await expect(git).toHaveAttribute("href", kaynakUrl);
    await expect(git).toHaveAttribute("target", "_blank");

    // Dış siteye gerçekten gidilmez: aynı adres yerel bir sayfayla karşılanır, sadece yeni sekmede açıldığı doğrulanır.
    await context.route(kaynakUrl, (route) => route.fulfill({ contentType: "text/html", body: "<title>kaynak</title>" }));
    const [sekme] = await Promise.all([context.waitForEvent("page"), git.click()]);
    await expect(sekme).toHaveURL(kaynakUrl);
    await sekme.close();
    await pencere.getByRole("button", { name: "Kapat" }).click();
  });

  await test.step("hesap sil", async () => {
    await page.goto("/profil");
    await page.getByRole("button", { name: "Hesabımı sil" }).click();
    const pencere = page.getByRole("dialog", { name: "Hesabın silinsin mi?" });
    await pencere.getByLabel("Şifre").fill(SIFRE);
    await pencere.getByRole("button", { name: "Hesabımı kalıcı olarak sil" }).click();
    await page.waitForURL(/\/giris/);
    await expect(page.getByText("Hesabın kapatıldı.", { exact: false })).toBeVisible();

    // Silinen hesapla tekrar giriş yapılamaz.
    await page.getByLabel("E-posta").fill(EPOSTA);
    await page.getByLabel("Şifre").fill(SIFRE);
    await page.getByRole("button", { name: "Giriş yap" }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/giris/);
  });
});

function escape(metin: string): string {
  return metin.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
