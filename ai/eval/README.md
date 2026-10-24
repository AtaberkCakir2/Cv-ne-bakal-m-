# ai/eval — Etiketli değerlendirme veri seti (T-019)

Yetkinlik çıkarımının doğruluğunu ölçmek için elle etiketlenmiş "altın standart" CV seti. T-018 (model benchmark'ı) ve T-055 (değerlendirme raporu: F1 ≥ 0,80) bu seti kullanır.

## Hedef (kabul kriteri)

- En az **50** anonimleştirilmiş CV: **TR + EN**, farklı formatlar, en az **5 taranmış** (görüntü) PDF.
- Her CV'nin yetkinlikleri **2 kişi** tarafından birbirinden bağımsız elle etiketlenir.
- Anlaşmazlıklar **3. kişi** tarafından çözülür → `gold/` dosyası.
- Gerçek CV'ler için sahiplerinden **yazılı izin** ([izin-formu.md](izin-formu.md)).

İlerleme durumunu her an görmek için: `python ai/eval/scripts/check_labels.py`

## Neyin nerede durduğu

| Ne | Nerede | Repoda mı? |
|---|---|---|
| CV PDF'leri (anonimleştirilmiş gerçek CV'ler) | Ekibe kapalı ortak klasör (Drive), `CareerAI/eval-cv/` | **Hayır** |
| İmzalı izin formları | Ekibe kapalı ortak klasör, `CareerAI/eval-izin/` | **Hayır** |
| Sentetik (uydurma) CV metinleri | `dataset/synthetic/` | Evet |
| CV listesi (kimlik içermez) | `dataset/manifest.csv` | Evet |
| Etiketler | `dataset/labels/<cv_id>/<etiketleyici>.json` | Evet |
| Altın standart (anlaşmazlık çözülmüş) | `dataset/gold/<cv_id>.json` | Evet |
| Geçici yetkinlik listesi | `dataset/skills_provisional.json` | Evet |

**Neden PDF'ler repoda değil:** Maskelemede tek bir hata kişisel veriyi git geçmişine kalıcı olarak yazar (CLAUDE.md kural 4, karar #9). Etiket dosyaları sadece CV kimliği ve yetkinlik adı içerir, kişisel veri içermez. Etiketlere CV'den alıntı **yazılmaz**.

## Süreç

1. **CV topla.** Gerçek CV için önce izin formu imzalatılır. CV'deki ad, telefon, e-posta, adres, TCKN, doğum tarihi, fotoğraf ve sosyal medya linkleri **elle** anonimleştirilir (PII modülü T-030 henüz yok). Dosya ortak klasöre `cv-NNN.pdf` adıyla konur; dosya adında kişinin adı geçmez.

   **Üstüne siyah kutu çizmek yetmez.** PDF düzenleyicide çizilen kutu alttaki metni silmez; kopyala-yapıştır veya `pdftotext` ile bilgiler geri gelir. Bu yüzden:
   - **Gerçek redaksiyon aracı** kullanın (ör. Acrobat "Redact" / "Karart" ve ardından "Uygula"), ya da PDF'i önce görüntüye çevirip yeniden PDF yapın. İkinci yol metin katmanını tamamen siler; bu dosya `scanned=true` olarak işaretlenir.
   - **PDF metadata'sını temizleyin:** Yazar (Author), Başlık (Title), Konu, Oluşturan uygulama alanlarında kişinin adı kalabilir (ör. Acrobat "Gizli bilgileri kaldır", ya da `exiftool -all= cv-NNN.pdf`).
   - **Kontrol edin:** `pdftotext cv-NNN.pdf -` çıktısında ad, telefon, e-posta, TCKN geçmemeli; dosya özelliklerinde (Author/Title) kişinin adı olmamalı. Kontrolden geçmeyen dosya ortak klasöre konmaz.
2. **Manifest'e satır ekle** (`dataset/manifest.csv`). Sütunlar aşağıda.
3. **Etiketle.** İki kişi CV'yi birbirinin etiketine bakmadan [etiketleme-kilavuzu.md](etiketleme-kilavuzu.md)'ye göre etiketler; her biri kendi dosyasını yazar.
4. **Uyumu ölç:** `python ai/eval/scripts/agreement.py` → CV bazında anlaşmazlık listesi ve genel uyum skoru.
5. **Anlaşmazlıkları çöz:** Üçüncü kişi anlaşmazlık listesine bakıp `gold/<cv_id>.json` dosyasını yazar. `agreement.py --write-gold` anlaşılan kısımlarla bir taslak üretir; üçüncü kişi sadece `"_karar_bekleyen"` listesini çözer.
6. **Kontrol:** `python ai/eval/scripts/check_labels.py` hata vermemeli.

### Etiketleyici atama

Üç kişi var; her CV'yi ikisi etiketler, üçüncüsü hakemdir. Yükü dengelemek için CV numarasına göre dönüşümlü:

| cv_id mod 3 | Etiketleyiciler | Hakem |
|---|---|---|
| 0 | burak, ataberk | anil |
| 1 | burak, anil | ataberk |
| 2 | ataberk, anil | burak |

## `manifest.csv` sütunları

| Sütun | Değerler | Açıklama |
|---|---|---|
| `cv_id` | `cv-001` … / sentetik için `syn-001` … | Kişiyle bağlantısı olmayan kimlik |
| `source` | `real`, `synthetic` | Gerçek (izinli, anonim) veya uydurma |
| `language` | `tr`, `en` | CV'nin ana dili |
| `layout` | `single_column`, `multi_column`, `table`, `creative` | Sayfa düzeni (T-020 çok sütunlu düzeni test eder) |
| `scanned` | `true`, `false` | Taranmış/görüntü PDF mi (OCR, T-029) |
| `pages` | sayı | Sayfa sayısı |
| `target_role` | ör. `backend-developer` | CV'nin uygun olduğu pozisyon (eşleştirme testleri için) |
| `consent_id` | ör. `IZN-007` / sentetik için boş | İmzalı izin formunun numarası (`source=real` için zorunlu) |

## Etiket dosyası formatı

`dataset/labels/cv-001/burak.json`:

```json
{
  "cv_id": "cv-001",
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

`agreement.py` iki etiketleyici arasında:

- **Yetkinlik F1** (CV bazında ve toplam micro-F1): biri bulup diğeri bulmadığında anlaşmazlık.
- **Seviye uyumu**: iki kişinin de bulduğu yetkinliklerde seviyenin aynı olma oranı ve Cohen's kappa.

Etiketleyiciler arası F1 0,85'in altındaysa kılavuz yetersiz demektir; kılavuz güncellenip etiketleme tekrar gözden geçirilir. Modelden bunu beklemek de anlamsız olur (hedef F1 ≥ 0,80).

## Taksonomi gelince

Ataberk'in taksonomisi (T-017) hazır olduğunda `skills_provisional.json` yerine o kullanılır. `check_labels.py --skills <yeni-dosya>` ile etiketler yeniden doğrulanır; adı değişen yetkinlikler toplu güncellenir.
