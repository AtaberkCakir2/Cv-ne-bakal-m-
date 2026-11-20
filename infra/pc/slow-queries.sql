-- Yavaş sorgu raporu (go-live #18: "yavaş sorgu yok, p95 < 50 ms"). `make prod-slow-queries` çalıştırır.
-- Kaynak pg_stat_statements (compose.yml'de shared_preload_libraries, eklenti deploy.sh setup_stats'ta). Sorgu metinleri
-- normalleştirilmiştir: sabitler $1, $2 olur, kullanıcı verisi görünmez.
-- pg_stat_statements yüzdelik vermez; "≈p95" = ortalama + 1,645 × standart sapma (normal dağılım varsayımı), kaba
-- tahmindir. Kesin p95 için Loki'deki istek süreleri kullanılır. Sıfırlamak (yeni ölçüm dönemi):
--   SELECT pg_stat_statements_reset();
\pset footer off
\echo
\echo '== Uygulama sorguları (careerai_app), ≈p95 en yüksek 15 =='
SELECT round(mean_exec_time::numeric, 1)                              AS ort_ms,
       round((mean_exec_time + 1.645 * stddev_exec_time)::numeric, 1) AS yaklasik_p95_ms,
       round(max_exec_time::numeric, 1)                               AS en_yuksek_ms,
       calls                                                          AS cagri,
       left(regexp_replace(query, '\s+', ' ', 'g'), 110)              AS sorgu
FROM pg_stat_statements s
JOIN pg_roles r ON r.oid = s.userid
WHERE r.rolname = 'careerai_app' AND s.calls >= 5
ORDER BY yaklasik_p95_ms DESC
LIMIT 15;

\echo '== Özet: ≈p95 50 ms üstü sorgu sayısı (hedef 0; çağrı >= 5) =='
SELECT count(*) FILTER (WHERE mean_exec_time + 1.645 * stddev_exec_time >= 50) AS yavas,
       count(*)                                                                AS toplam,
       (SELECT stats_reset FROM pg_stat_statements_info)                       AS olcum_baslangici
FROM pg_stat_statements s
JOIN pg_roles r ON r.oid = s.userid
WHERE r.rolname = 'careerai_app' AND s.calls >= 5;
