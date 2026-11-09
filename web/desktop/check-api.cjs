// Kurulum dosyası üretilmeden önce: API adresi derlemeye gömülür (VITE_API_URL). Verilmezse uygulama 127.0.0.1'e
// bağlanmaya çalışır ve paketli uygulamanın CSP'si bunu engeller; giriş ekranı "Sunucuya ulaşılamadı" der.
const url = process.env.VITE_API_URL ?? "";
if (!url.startsWith("https://")) {
  console.error("VITE_API_URL https:// ile başlamalı, ör. https://api.cvnebakalim.com (web/desktop/README.md)");
  process.exit(1);
}
