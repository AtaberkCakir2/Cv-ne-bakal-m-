// Hata bildirme kanalı (Go-Live #47, beta/UAT planı T-078: docs/uat/beta-uat-plani.md).
// Form yerine e-posta: backend'de ek uç ve saklama gerekmez; gelen kutusu ekipte.
export const SUPPORT_EMAIL = "iletisim@cvnebakalim.com";

/**
 * Önceden doldurulmuş hata bildirimi e-postası. Sayfa yolu eklenir, sorgu dizesi eklenmez
 * (bağlantı token'ları orada olabilir). CV ve kişisel bilgi istenmez.
 */
export function bugReportHref(path: string): string {
  const subject = "Hata bildirimi";
  const body = [
    "Ne yapıyordunuz?",
    "",
    "Ne olmasını bekliyordunuz, ne oldu?",
    "",
    "Hata kodu (ekranda görünüyorsa):",
    "",
    `Sayfa: ${path}`,
    `Tarayıcı: ${navigator.userAgent}`,
    "",
    "Lütfen CV'nizi, şifrenizi veya kişisel bilgilerinizi eklemeyin.",
  ].join("\n");
  return `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
