/**
 * Yüzdeye Türkçe iyelik eki: %75'i, %40'ı, %10'u, %20'si, %100'ü. Ek, sayının okunuşundaki son kelimeye göre
 * seçilir: son basamak 0 değilse birler ("yetmiş beş" → beş → 'i), 0 ise onlar ("kırk" → 'ı), tam 100 "yüz" → 'ü.
 */
const ONES = ["", "'i", "'si", "'ü", "'ü", "'i", "'sı", "'si", "'i", "'u"]; // bir, iki, üç, dört, beş, altı, yedi, sekiz, dokuz
const TENS = ["", "'u", "'si", "'u", "'ı", "'si", "'ı", "'i", "'i", "'ı"]; // on, yirmi, otuz, kırk, elli, altmış, yetmiş, seksen, doksan

export function percentOf(ratio: number): string {
  const n = Number.isFinite(ratio) ? Math.round(Math.min(1, Math.max(0, ratio)) * 100) : 0;
  const suffix = n === 0 ? "'ı" : n === 100 ? "'ü" : n % 10 ? ONES[n % 10] : TENS[Math.floor(n / 10)];
  return `%${n}${suffix}`;
}

/** Sadece http(s) adresler link olur (backend de süzer; burada ikinci savunma). */
export function isWebUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}
