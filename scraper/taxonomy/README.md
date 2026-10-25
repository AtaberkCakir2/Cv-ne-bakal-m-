# Yetkinlik taksonomisi ve hedef pozisyonlar (T-017)

Tek doğru kaynak bu klasördeki iki CSV. Veritabanına `python -m collector seed-taxonomy` ile yazılır (`skills`, `roles` tabloları); aynı CSV ile tekrar çalıştırmak hiçbir şeyi değiştirmez. CSV'den çıkarılan kayıt silinmez, `is_active=false` olur (ilan ve analizler ona bağlı olabilir).

| Dosya | Kayıt | İçerik |
|---|---|---|
| `skills.csv` | 374 yetkinlik | dil 45 · framework 79 · veritabanı 36 · bulut 29 · devops 36 · araç 78 · metodoloji 57 · soft 14 |
| `roles.csv` | 12 pozisyon | Backend, Frontend, Full-Stack, Mobil, Veri Bilimci, DevOps, QA, ML Mühendisi, Siber Güvenlik, Oyun + Veri Mühendisi, Veri Analisti |

## skills.csv sütunları

| Sütun | Kural |
|---|---|
| `canonical_name` | Standart ad; `contracts/` içindeki `skills[].skill` bu addır. Tekil. |
| `slug` | `a-z0-9` ve `-`; tekil, değişmez (etiketler ve analizler buna bağlı). |
| `category` | `dil`, `framework`, `veritabani`, `bulut`, `devops`, `arac`, `metodoloji`, `soft` |
| `synonyms` | `|` ile ayrılmış, **küçük harf**. Bir terim (ad veya eş anlamlı) sadece bir yetkinliğe ait olabilir. Türkçe karşılıklar da burada ("birim test", "makine öğrenimi"). |
| `esco_uri` | ESCO kavram URI'si (aşağıda "ESCO"). Elle girilen URI'ye eşleme komutu dokunmaz. |
| `case_sensitive` | `1` ise **ad sadece yazıldığı gibi** eşleşir: `SOLID` evet, "solid understanding" hayır. Adı sıradan kelime olan teknolojiler (Go, Swift, Rust, Spring Boot, Express.js, Unity, Snowflake…). Eş anlamlılar (golang, spring framework) yine harf duyarsız; bu yüzden harf duyarlı bir yetkinliğin eş anlamlısı adının küçük hali olamaz. Veritabanında sütunu yok; eşleyici (T-031) CSV'den veya JSON çıktısından okur. |

`python -m collector export-taxonomy --out taxonomy.json` → `ai/eval/dataset/skills_provisional.json` ile aynı biçim (+ `case_sensitive: true`).

## ESCO

**61 / 374 yetkinlik** ESCO v1.2.1 kavramına bağlı (ör. Python → "Python (computer programming)", Jenkins → "Jenkins (tools for software configuration management)", PostgreSQL, Unity, deep learning, English). ESCO genel bir sınıflandırma; çoğu framework ve bulut servisi (React, Next.js, Kubernetes, AWS…) ESCO'da kendi kavramı olarak yok, onlar elle derlendi.

- **Eşleme:** `python -m collector map-esco --csv data/esco/skills_en.csv`. Sadece ESCO'nun **tercih edilen adıyla** birebir eşleşme (sondaki parantezli açıklama yok sayılır). Alternatif adlar kullanılmaz: ESCO onları geniş kavramlarda toplar ("computer programming" kavramının alternatifleri arasında bash ve OCaml, "computer vision"ınkiler arasında tensorflow var); ilk denemede bu yüzden ~20 yanlış eşleşme çıkmıştı. Aynı adlı başka kavramlar `collector/esco.py` içindeki `HOMONYMS` listesinde (ör. ESCO'daki SPARK bir Java micro framework'ü, Apache Spark değil). Eşleşmeler elle gözden geçirildi.
- **Veri:** ESCO indirme sayfasından (https://esco.ec.europa.eu/en/use-esco/download) "ESCO dataset v1.2.1 · Classification · English · CSV"; e-posta ile link gelir. Dosya repoya girmez (`scraper/data/` git dışı).
- **Lisans:** [ESCO SSS](https://esco.ec.europa.eu/en/about-esco/faq): 2011/833/EU kararı uyarınca her amaçla ücretsiz kullanılabilir, başka sınıflandırmalarla eşlenebilir; **kaynak gösterilmesi şart**. Uygulamada: *"This service uses the ESCO classification of the European Commission."* Rapor ve sunumlarda: *"This publication uses the ESCO classification of the European Commission."* ESCO kavram adları değiştirilmez (biz sadece URI saklıyoruz).

## Nasıl doğrulandı

- `tests/test_taxonomy.py`: tekil slug/ad/eş anlamlı, kategori, ≥ 300 yetkinlik, istenen 10 pozisyon, `contracts/examples` yetkinlikleri ve Burak'ın 82 geçici yetkinliği (ad + slug + kategori aynı).
- **2.048 gerçek ilanla kapsam** (25.10.2026, basit sözcük sınırı eşlemesi): ilanların %85,9'unda en az bir yetkinlik, ilan başına ortalama 7,3. En sık: Python 609, React 463, TypeScript 460, AWS 387, PostgreSQL 350. Analizle eklenenler: Anthropic Claude (140 ilan), Cursor (68), GitHub Copilot (53), Yazılım Testi (54). `case_sensitive` ile düzelen yanlış pozitif örnekleri: SOLID 171 → 17 ilan, Next.js'in "next" eş anlamlısı kaldırıldı.

## Yetkinlik eklerken

1. `skills.csv`'ye satır ekle (slug'ı sonradan değiştirme).
2. `pytest tests/test_taxonomy.py` — çakışan eş anlamlı veya biçim hatası burada yakalanır.
3. `python -m collector seed-taxonomy`.
4. Adı sıradan bir kelimeyse `case_sensitive=1`.
