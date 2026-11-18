/** Girişten sonra dönülecek sayfa; sadece site içi yol kabul edilir (açık yönlendirme olmasın). */
export function safeNext(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) return "/yukle";
  // "/\t/evil.com" gibi değerler ayrıştırılınca başka siteye dönüşebilir; sonuç aynı sitede kalmalı.
  try {
    return new URL(value, window.location.origin).origin === window.location.origin ? value : "/yukle";
  } catch {
    return "/yukle";
  }
}
