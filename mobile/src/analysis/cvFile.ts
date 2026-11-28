import { File, Paths } from "expo-file-system";

/**
 * Yüklemeden önce istemci tarafı kontrol (web/src/analysis/cvFile.ts ile aynı sınırlar). Asıl kontrol backend'de
 * (sayfa sayısı, şifre, bozuk dosya, "%PDF-" imzası); burada amaç kullanıcıyı boşuna beklememek.
 */
export const MAX_CV_BYTES = 5 * 1024 * 1024;
export const MAX_CV_PAGES = 5;

export interface PickedFile {
  uri: string;
  name: string;
  size?: number;
  mimeType?: string;
}

/**
 * Seçilen PDF'in uygulama önbelleğindeki kopyasını siler (PR #161 incelemesi, CLAUDE.md kural 5: CV dosyası saklanmaz).
 * expo-document-picker Android'de content:// adresini okuyabilmek için dosyayı önbelleğe kopyalar; kopya yükleme
 * bitince, başka dosya seçilince ve ekrandan çıkınca silinir. Sadece önbellekteki dosyalara dokunur (kullanıcının asıl
 * dosyası silinmez); silinemezse hata yutulur, işletim sistemi önbelleği zaten temizler.
 */
export function discardCvCopy(file: PickedFile | undefined): void {
  if (!file || !file.uri.startsWith(Paths.cache.uri)) return;
  try {
    const copy = new File(file.uri);
    if (copy.exists) copy.delete();
  } catch {
    // silinemedi; önbellek dosyası, OS temizler
  }
}

/** Dosya uygunsa undefined, değilse kullanıcıya gösterilecek mesaj. */
export function cvFileError(file: PickedFile): string | undefined {
  const pdf = file.mimeType === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  if (!pdf) return "Sadece PDF dosyası yükleyebilirsin.";
  if (file.size === 0) return "Dosya boş görünüyor.";
  if (file.size !== undefined && file.size > MAX_CV_BYTES) return `Dosya ${formatSize(file.size)}; en fazla 5 MB olabilir.`;
  return undefined;
}

export function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} MB`;
}

/** Retry-After (saniye) → "38 dakika" / "45 saniye". */
export function formatWait(seconds: number): string {
  if (seconds >= 90) return `${Math.ceil(seconds / 60)} dakika`;
  return `${Math.max(1, Math.round(seconds))} saniye`;
}

export function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m ? `${m} dk ${s} sn` : `${s} sn`;
}
