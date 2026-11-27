# ai/eval — Etiketli değerlendirme veri seti (T-019)

Yetkinlik çıkarımının doğruluğunu ölçmek için elle etiketlenmiş "altın standart" CV seti. **Tamamen sentetiktir: gerçek kişilere ait CV toplanmaz (karar #20).** T-018 (model benchmark'ı) ve T-055 (değerlendirme raporu: F1 ≥ 0,80) bu seti kullanır.

## Hedef (kabul kriteri)

- **50 sentetik CV:** 25 TR + 25 EN · 10 pozisyon × 5 · tek ve çok sütunlu · en az **5 taranmış** (görüntü) PDF · yeni mezun / stajyer / deneyimli dengeli.
- **Etiketleme (karar #40, 22.11.2026):** 50 CV'nin hepsini **Claude** etiketler (`labels/<cv_id>/claude.json`); gold başlangıçta bu etikettir. Ekipten her kişi kendi atamasından **3–4 CV'yi kontrol eder** ve düzeltilmiş hâlini gold'a kendi adıyla yazar (aşağıda "Kontrol"). Raporlarda (T-055, T-081) etiketlerin yapay zekayla üretildiği ve kaç CV'nin kontrol edildiği yazılır.
- ~~Her CV en az 1 kişi; 20 CV ikinci kişi tarafından da bağımsız etiketlenir; anlaşmazlıkları 3. kişi çözer.~~ Karar #40 ile kaldırıldı. Aşağıdaki çift etiket maddeleri ve atama tablosu, kontrol edilecek CV'leri seçmek için duruyor.
- **Çift etiketlenen 20 CV dengeli seçilir:** en az 8 TR + 8 EN, en az 6 çok sütunlu, en az 2 taranmış, üç deneyim düzeyinden de.
- Çift etiketli alt kümede etiketleyiciler arası **F1 ≥ 0,85**.
- İlk **10 Türkçe CV** önceliklidir (T-018 benchmark'ı).

Plan: #30'da Ataberk'le kararlaştırıldı (29.10.2026). Görev durumu: `docs/gorevler/burak.md` → T-019.

İlerleme durumunu her an görmek için: `python ai/eval/scripts/check_labels.py`

## Neyin nerede durduğu

| Ne | Nerede | Repoda mı? |
|---|---|---|
| CV tanım dosyaları (kaynak) | `dataset/cv_specs/<cv_id>.json` | Evet |
| Sentetik CV PDF'leri | `dataset/synthetic/<cv_id>.pdf` (`generate_cvs.py` üretir; elle düzenlenmez) | Evet |
| İlk 3 örnek CV (sadece metin, PDF'i yok; veri setine sayılmaz) | `examples/synthetic/syn-001..003.md` | Evet |
| Şablon girdisi (pozisyon × yetkinlik × eş anlamlı) | `dataset/template_input.json` (Ataberk, `scraper/`'dan) | Evet |
| CV listesi (kimlik içermez) | `dataset/manifest.csv` | Evet |
| Etiketler | `dataset/labels/<cv_id>/<etiketleyici>.json` | Evet |
| Altın standart (anlaşmazlık çözülmüş) | `dataset/gold/<cv_id>.json` | Evet |
| Yetkinlik listesi | `scraper/taxonomy/skills.csv` (Ataberk, T-017); `dataset/skills_provisional.json` sadece testlerde | Evet |

**Kişisel veri yok:** CV'lerdeki ad, okul, şirket ve iletişim bilgileri uydurmadır; her CV repoya girmeden önce gerçek bir kişiye ait bilgi içermediği elle kontrol edilir. CV üretiminde bir ÜYZ aracı kullanılırsa adı ve sürümü TÜBİTAK beyanına yazılır.

## Süreç

1. **CV üret.** Her CV için `dataset/cv_specs/<cv_id>.json` tanımı yazılır (iskelet `template_input.json`'daki pozisyon × yetkinlik listesinden; proje ve deneyim metinlerini insan yazar). Yetkinlikler metinde açık liste olarak, proje açıklaması içinde ve kısaltma/yazım farklılıklarıyla ("JS", "k8s", "Postgres", yazım hatası, TR-EN karışık) geçer. PDF ve manifest satırı `generate_cvs.py` ile üretilir (aşağıda); `scanned: true` olan CV görüntüye çevrilip yeniden PDF yapılır.
   - **Şablonun yetkinlik listesi cevap anahtarı değildir.** Etiketler metinde gerçekten geçene göre, sıfırdan ve elle verilir; bir eşleyicinin (ör. `scraper/etl/skills.py`) çıktısı ön etiket olarak kullanılmaz. Aksi halde TÜBİTAK İP3'teki yöntem karşılaştırması geçersizleşir.
2. **Manifest'e satır ekle** (`dataset/manifest.csv`). Sütunlar aşağıda.
3. **Etiketle.** *(Karar #40'tan beri etiketleri Claude veriyor; bu adım kontrol edilecek CV'ler ve ileride eklenecek insan etiketleri için.)* Her CV'yi bir kişi [etiketleme-kilavuzu.md](etiketleme-kilavuzu.md)'ye göre etiketler. Çift etiket için seçilen 20 CV'yi ikinci kişi de, birinci kişinin etiketine bakmadan etiketler; her biri kendi dosyasını yazar.
4. **Uyumu ölç:** `python ai/eval/scripts/agreement.py` → çift etiketli CV'lerde anlaşmazlık listesi ve genel uyum skoru.
5. **Gold'u yaz:** `agreement.py --write-gold` çift etiketli CV'ler için anlaşılan kısımlarla bir taslak üretir; üçüncü kişi sadece `"_karar_bekleyen"` listesini çözer. Tek etiketli CV'lerde etiket olduğu gibi gold'a kopyalanır.
6. **Kontrol:** `python ai/eval/scripts/check_labels.py` hata vermemeli.

### Kontrol (karar #40)

Claude etiketinin kalitesini görmek için her kişi kendi atamasındaki (aşağıdaki tablo, 1. etiketleyici sütunu) **3–4 CV**'yi kontrol eder; tercihen biri Türkçe, biri İngilizce, biri çok sütunlu veya taranmış olsun.

1. CV'yi `dataset/synthetic/<cv_id>.pdf`'ten oku, [etiketleme-kilavuzu.md](etiketleme-kilavuzu.md)'yi aç.
2. `dataset/gold/<cv_id>.json`'da eksik yetkinliği ekle, yanlış olanı sil, seviyeyi/yılı düzelt.
3. `"adjudicator"` alanına kendi adını yaz, `"notes"`'a kaç ekleme/silme/seviye düzeltmesi yaptığını yaz (ör. `"kontrol: +2 −1 seviye 3"`). `labels/<cv_id>/claude.json`'a dokunma: kontrolde ne düzeltildiği bu ikisinin farkından ölçülür.
4. `python ai/eval/scripts/check_labels.py` hata vermemeli.

### Etiketleyici atama

Yükü dengelemek için CV numarasına göre dönüşümlü. Tek etiketli CV'yi tablodaki **ilk** kişi etiketler; çift etiketli 20 CV'de ikinci kişi de etiketler, hakem anlaşmazlıkları çözer:

| cv_id mod 3 | 1. etiketleyici | 2. etiketleyici (çift etiketlilerde) | Hakem |
|---|---|---|---|
| 0 | burak | ataberk | anil |
| 1 | burak | anil | ataberk |
| 2 | ataberk | anil | burak |

## CV tanım dosyası

Her sentetik CV `dataset/cv_specs/<cv_id>.json` dosyasıdır; PDF ve manifest satırı bundan üretilir:

```bash
python ai/eval/scripts/generate_cvs.py              # hepsi
python ai/eval/scripts/generate_cvs.py --only syn-014
```

```json
{
  "cv_id": "syn-014", "language": "tr", "layout": "multi_column", "scanned": false,
  "target_role": "backend-developer", "experience": "intern", "double": false,
  "header": {"name": "Ad Soyad", "title": "Unvan", "contact": ["ad@example.com", "0532 000 00 00", "Şehir"]},
  "sidebar": [{"title": "Beceriler", "list": ["Python — ileri", "Docker"]}],
  "main": [
    {"title": "Hakkımda", "text": ["Paragraf..."]},
    {"title": "Deneyim", "items": [{"heading": "Pozisyon — Şirket (örnek)", "meta": "2025 – halen", "bullets": ["..."]}]}
  ]
}
```

- `layout`: `single_column` veya `multi_column` (sol kenar çubuğu = `sidebar`; ilk sayfaya sığmalı, sığmazsa script hata verir).
- `scanned: true` → sayfalar 150 DPI gri tonlu görüntüye çevrilir, metin katmanı kalmaz (OCR testi, T-029).
- Bölüm türleri: `text` (paragraflar), `items` (başlık + `meta` + `text`/`bullets`), `list` (madde listesi).
- **Kişisel veri:** ad uydurma; e-posta sadece `example.com/org/net`; telefon `05xx 000 xx xx` (000 bloklu); şirket adlarında "örnek/Ornek"; web adresleri `*.example.com`. T-030 (kişisel veri maskeleme) bu alanları maskelemeyi test eder.
- **Çeşitlilik:** yetkinlikler hem listede hem cümle içinde; kısaltmalar (JS, TS, k8s, Postgres, sklearn), seviye ifadeleri ("ileri düzey", ★★★☆☆, B2, "3 yıl"), istek cümleleri ("öğrenmek istiyorum"), sadece ders adı geçen konular; bunlar etiketleme kılavuzunun kurallarını sınar.

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

- `skill`: taksonomideki (`scraper/taxonomy/skills.csv`) `canonical_name` ile **birebir** aynı. Listede olmayan yetkinlik için kılavuzdaki kurala bak.
- `level`: `beginner`, `intermediate`, `advanced`, `unknown` — `contracts/analysis_result.schema.json` ile aynı değerler.
- `years`: CV'de açıkça yazıyorsa sayı, yoksa `null`.

`gold/` dosyaları aynı formattadır; `annotator` yerine `adjudicator` alanı vardır.

## Ölçüm

`agreement.py` çift etiketli CV'lerde iki etiketleyici arasında:

- **Yetkinlik F1** (CV bazında ve toplam micro-F1): biri bulup diğeri bulmadığında anlaşmazlık.
- **Seviye uyumu**: iki kişinin de bulduğu yetkinliklerde seviyenin aynı olma oranı ve Cohen's kappa.

Etiketleyiciler arası F1 0,85'in altındaysa kılavuz yetersiz demektir; kılavuz güncellenip etiketleme tekrar gözden geçirilir. Modelden bunu beklemek de anlamsız olur (hedef F1 ≥ 0,80).

**Model değerlendirmesi (T-055):** `evaluate.py run --tag <ad>` CV'leri üretimdeki çıkarım zincirinden geçirir (Ollama gerekir), `evaluate.py report --tag <ad>` gold'a göre kesinlik/duyarlılık/F1, seviye doğruluğu ve gecikmeyi basar. Sonuçlar [`results/`](results/), rapor [`report.md`](report.md).

## Taksonomi değişince

`check_labels.py` ve `agreement.py` varsayılan olarak Ataberk'in taksonomisini (T-017, `scraper/taxonomy/skills.csv`) kullanır; ilk 82 yetkinlikli geçici liste (`skills_provisional.json`) sadece örnek etiketlerin testlerinde kalır. Taksonomi değişince `check_labels.py` etiketleri yeniden doğrular; adı değişen yetkinlikler toplu güncellenir.
