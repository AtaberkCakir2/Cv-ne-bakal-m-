import type { components } from "../api/schema";

type Resource = components["schemas"]["ResourceOut"];

/** Metinler web/src/analysis/ResultDashboard.tsx ile aynı. */
export const LEVEL: Record<string, string> = {
  beginner: "başlangıç",
  intermediate: "orta",
  advanced: "ileri",
  unknown: "seviye belirsiz",
};
export const PROVIDER: Record<string, string> = {
  youtube: "YouTube",
  udemy: "Udemy",
  coursera: "Coursera",
  btk_akademi: "BTK Akademi",
  docs: "Dokümantasyon",
  blog: "Blog",
  other: "Diğer",
};
export const LANGUAGE: Record<string, string> = { tr: "Türkçe", en: "İngilizce" };

/** İlan sayısı bunun altındaysa oranlar daha az güvenilir (risk R-11). */
export const LOW_DATA_POSTINGS = 50;

/**
 * Yüzdeye Türkçe iyelik eki: %75'i, %40'ı, %10'u, %20'si, %100'ü (web/src/analysis/format.ts ile aynı).
 * Ek, sayının okunuşundaki son kelimeye göre seçilir.
 */
const ONES = ["", "'i", "'si", "'ü", "'ü", "'i", "'sı", "'si", "'i", "'u"];
const TENS = ["", "'u", "'si", "'u", "'ı", "'si", "'ı", "'i", "'i", "'ı"];
export function percentOf(ratio: number): string {
  const n = Number.isFinite(ratio) ? Math.round(Math.min(1, Math.max(0, ratio)) * 100) : 0;
  const suffix = n === 0 ? "'ı" : n === 100 ? "'ü" : n % 10 ? ONES[n % 10] : TENS[Math.floor(n / 10)];
  return `%${n}${suffix}`;
}

/** "150 ilanın %75'i istiyor" — ilan sayısı bilinmiyorsa "ilanların %75'i istiyor". */
export function demandText(ratio: number, postings: number | null | undefined): string {
  return postings ? `${postings} ilanın ${percentOf(ratio)} istiyor` : `ilanların ${percentOf(ratio)} istiyor`;
}

/** Sadece http(s) adresler açılır (backend de süzer; burada ikinci savunma). */
export function isWebUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

export function resourceMeta(r: Resource): string {
  return [
    LEVEL[r.level],
    r.duration_min != null && `${r.duration_min} dk`,
    r.is_free ? "ücretsiz" : "ücretli",
    r.language && LANGUAGE[r.language],
  ]
    .filter(Boolean)
    .join(" · ");
}

export function formatDate(iso: string, withTime = false): string {
  return new Date(iso).toLocaleString("tr-TR", {
    day: "numeric",
    month: withTime ? "short" : "long",
    year: "numeric",
    ...(withTime && { hour: "2-digit", minute: "2-digit" }),
  });
}
