# ai/eval — Etiketli değerlendirme veri seti (T-019)

Yetkinlik çıkarımının doğruluğunu ölçmek için elle etiketlenmiş "altın standart" CV seti. **Tamamen sentetiktir: gerçek kişilere ait CV toplanmaz (karar #20).** T-018 (model benchmark'ı) ve T-055 (değerlendirme raporu: F1 ≥ 0,80) bu seti kullanır.

## Hedef (kabul kriteri)

- **50 sentetik CV:** 25 TR + 25 EN · 10 pozisyon × 5 · tek ve çok sütunlu · en az **5 taranmış** (görüntü) PDF · yeni mezun / stajyer / deneyimli dengeli.
- **Etiketleme:** her CV en az **1 kişi**; **20 CV** ikinci bir kişi tarafından da bağımsız etiketlenir. İkili etiketlerdeki anlaşmazlıkları **3. kişi** çözer → `gold/` dosyası.
- **Çift etiketlenen 20 CV dengeli seçilir:** en az 8 TR + 8 EN, en az 6 çok sütunlu, en az 2 taranmış, üç deneyim düzeyinden de.
- Çift etiketli alt kümede etiketleyiciler arası **F1 ≥ 0,85**.
- İlk **10 Türkçe CV** önceliklidir (T-018 benchmark'ı).

Plan: #30'da Ataberk'le kararlaştırıldı (29.10.2026). Görev durumu: `docs/gorevler/burak.md` → T-019.

İlerleme durumunu her an görmek için: `python ai/eval/scripts/check_labels.py`

## Neyin nerede durduğu

| Ne | Nerede | Repoda mı? |
|---|---|---|
| Sentetik CV metinleri (kaynak) | `dataset/synthetic/<cv_id>.md` | Evet |
| Sentetik CV PDF'leri | `dataset/synthetic/<cv_id>.pdf` (şablon betiği üretir) | Evet |
| Şablon girdisi (pozisyon × yetkinlik × eş anlamlı) | `dataset/template_input.json` (Ataberk, `scraper/`'dan) | Evet |
| CV listesi (kimlik içermez) | `dataset/manifest.csv` | Evet |
| Etiketler | `dataset/labels/<cv_id>/<etiketleyici>.json` | Evet |
| Altın standart (anlaşmazlık çözülmüş) | `dataset/gold/<cv_id>.json` | Evet |
| Geçici yetkinlik listesi | `dataset/skills_provisional.json` | Evet |

**Kişisel veri yok:** CV'lerdeki ad, okul, şirket ve iletişim bilgileri uydurmadır; her CV repoya girmeden önce gerçek bir kişiye ait bilgi içermediği elle kontrol edilir. CV üretiminde bir ÜYZ aracı kullanılırsa adı ve sürümü TÜBİTAK beyanına yazılır.

## Süreç

1. **CV üret.** Şablon betiği `template_input.json`'dan CV iskeletini kurar (ad, okul, pozisyon, yetkinlik listesi, düzen); proje ve deneyim metinlerini insan yazar. Yetkinlikler metinde açık liste olarak, proje açıklaması içinde ve kısaltma/yazım farklılıklarıyla ("JS", "k8s", "Postgres", yazım hatası, TR-EN karışık) geçer. Taranmış olacak CV'ler PDF'ten görüntüye çevrilip yeniden PDF yapılır (`scanned=true`).
   - **Şablonun yetkinlik listesi cevap anahtarı değildir.** Etiketler metinde gerçekten geçene göre, sıfırdan ve elle verilir; bir eşleyicinin (ör. `scraper/etl/skills.py`) çıktısı ön etiket olarak kullanılmaz. Aksi halde TÜBİTAK İP3'teki yöntem karşılaştırması geçersizleşir.
2. **Manifest'e satır ekle** (`dataset/manifest.csv`). Sütunlar aşağıda.
3. **Etiketle.** Her CV'yi bir kişi [etiketleme-kilavuzu.md](etiketleme-kilavuzu.md)'ye göre etiketler. Çift etiket için seçilen 20 CV'yi ikinci kişi de, birinci kişinin etiketine bakmadan etiketler; her biri kendi dosyasını yazar.
4. **Uyumu ölç:** `python ai/eval/scripts/agreement.py` → çift etiketli CV'lerde anlaşmazlık listesi ve genel uyum skoru.
5. **Gold'u yaz:** `agreement.py --write-gold` çift etiketli CV'ler için anlaşılan kısımlarla bir taslak üretir; üçüncü kişi sadece `"_karar_bekleyen"` listesini çözer. Tek etiketli CV'lerde etiket olduğu gibi gold'a kopyalanır.
6. **Kontrol:** `python ai/eval/scripts/check_labels.py` hata vermemeli.

### Etiketleyici atama

Yükü dengelemek için CV numarasına göre dönüşümlü. Tek etiketli CV'yi tablodaki **ilk** kişi etiketler; çift etiketli 20 CV'de ikinci kişi de etiketler, hakem anlaşmazlıkları çözer:

| cv_id mod 3 | 1. etiketleyici | 2. etiketleyici (çift etiketlilerde) | Hakem |
|---|---|---|---|
| 0 | burak | ataberk | anil |
| 1 | burak | anil | ataberk |
| 2 | ataberk | anil | burak |

## `manifest.csv` sütunları

| Sütun | Değerler | Açıklama |
|---|---|---|
| `cv_id` | `syn-001` … | Kimlik |
| `source` | `synthetic` | Karar #20'den beri sadece `synthetic` (`real` sütun değeri eski kayıtlar için kodda duruyor) |
| `language` | `tr`, `en` | CV'nin ana dili |
| `layout` | `single_column`, `multi_column`, `table`, `creative` | Sayfa düzeni (T-020 çok sütunlu düzeni test eder) |
| `scanned` | `true`, `false` | Taranmış/görüntü PDF mi (OCR, T-029) |
| `pages` | sayı | Sayfa sayısı |
| `target_role` | ör. `backend-developer` | CV'nin uygun olduğu pozisyon (`scraper/taxonomy/roles.csv` slug'ı) |
| `experience` | `new_grad`, `intern`, `experienced` | Deneyim düzeyi (dağılım kontrolü için) |
| `double` | `true`, `false` | Çift etiket için seçildi mi |
| `consent_id` | boş | Eski sütun; sentetik CV'de boş kalır |

## Etiket dosyası formatı

`dataset/labels/syn-001/burak.json`:

```json
{
  "cv_id": "syn-001",
  "annotator": "burak",
  "skills": [
    { "skill": "Python", "level": "advanced", "years": 3 },
    { "skill": "Docker", "level": "unknown", "years": null }
  ],
  "notes": ""
}
```

- `skill`: `skills_provisional.json`'daki `canonical_name` ile **birebir** aynı. Listede olmayan yetkinlik için kılavuzdaki kurala bak.
- `level`: `beginner`, `intermediate`, `advanced`, `unknown` — `contracts/analysis_result.schema.json` ile aynı değerler.
- `years`: CV'de açıkça yazıyorsa sayı, yoksa `null`.

`gold/` dosyaları aynı formattadır; `annotator` yerine `adjudicator` alanı vardır.

## Ölçüm

`agreement.py` çift etiketli CV'lerde iki etiketleyici arasında:

- **Yetkinlik F1** (CV bazında ve toplam micro-F1): biri bulup diğeri bulmadığında anlaşmazlık.
- **Seviye uyumu**: iki kişinin de bulduğu yetkinliklerde seviyenin aynı olma oranı ve Cohen's kappa.

Etiketleyiciler arası F1 0,85'in altındaysa kılavuz yetersiz demektir; kılavuz güncellenip etiketleme tekrar gözden geçirilir. Modelden bunu beklemek de anlamsız olur (hedef F1 ≥ 0,80).

## Taksonomi gelince

Ataberk'in taksonomisi (T-017) hazır olduğunda `skills_provisional.json` yerine o kullanılır. `check_labels.py --skills <yeni-dosya>` ile etiketler yeniden doğrulanır; adı değişen yetkinlikler toplu güncellenir.
