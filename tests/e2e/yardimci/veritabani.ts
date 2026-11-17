import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ORTAM = fileURLToPath(new URL("../ortam.sh", import.meta.url));

/** E2E veritabanında SQL çalıştırır, çıktıyı döner (ortam.sh psql: -t -A, satır başına bir sonuç). */
export function sql(sorgu: string): string {
  return execFileSync("bash", [ORTAM, "psql"], { input: sorgu, encoding: "utf-8" }).trim();
}

/**
 * GEÇİCİ (T-057 gelene kadar): geliştirme ortamındaki örnek analiz (ExampleAnalyzer) sadece eşleşme skorunu yazar,
 * eksik yetkinlik ve kaynak önerisi üretmez. "Kaynak aç" adımı test edilebilsin diye, sözleşmedeki örnekle aynı
 * biçimde (contracts/examples/analysis_result.example.json: missing_skills[0] = Docker, öncelik 1, bir kaynak)
 * analize bir eksik yetkinlik ve ona ait bir kaynak eklenir. Gerçek AI akışı bağlanınca bu çağrı silinir.
 */
export function eksikYetkinlikVeKaynakEkle(analizId: string): { kaynakBasligi: string; kaynakUrl: string } {
  if (!/^[0-9a-f-]{36}$/.test(analizId)) throw new Error(`Beklenmeyen analiz kimliği: ${analizId}`);
  const satir = sql(`
    WITH k AS (
      SELECT id AS resource_id, skill_id, title, url FROM resources
      WHERE is_alive AND url LIKE 'https://%' ORDER BY id LIMIT 1
    ), s AS (
      INSERT INTO analysis_skills (analysis_id, skill_id, kind, demand_ratio, priority)
      SELECT '${analizId}', skill_id, 'missing', 0.75, 1 FROM k RETURNING skill_id
    ), o AS (
      INSERT INTO analysis_recommendations (analysis_id, skill_id, resource_id, rank, reason_text)
      SELECT '${analizId}', k.skill_id, k.resource_id, 1, 'E2E: sözleşme örneğindeki gibi bir öneri' FROM k
      RETURNING resource_id
    )
    SELECT k.title || E'\t' || k.url FROM k, s, o;
  `);
  const [kaynakBasligi, kaynakUrl] = satir.split("\t");
  if (!kaynakBasligi || !kaynakUrl) throw new Error("Kaynak eklenemedi: resources-seed çalıştı mı?");
  return { kaynakBasligi, kaynakUrl };
}
