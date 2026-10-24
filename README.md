# CareerAI

Yapay zeka destekli kariyer ve eğitim yönlendirme sistemi. Öğrencinin CV'sini hedef pozisyondaki güncel iş ilanlarıyla karşılaştırır, eksik yetkinlikleri bulur ve bu eksikleri kapatacak eğitim kaynaklarını önerir.

**Ekip:** Ataberk (veri, veri tabanı, DevOps) · Burak (yapay zeka / NLP, mobil) · Anıl (backend API, web/masaüstü)

## Kurulum

Gerekenler: Git, Docker Desktop, Python 3.12, Node.js 20+.

```bash
git clone https://github.com/AtaberkCakir2/Cv-ne-bakal-m-.git
cd Cv-ne-bakal-m-
# .env dosyasını aşağıdaki "Ortam değişkenleri" bölümüne göre oluşturun
docker compose up -d        # Postgres, Redis ve Ollama'yı başlatır
docker compose exec ollama ollama pull llama3.1:8b
```

### Ortam değişkenleri

Proje kök dizininde `.env` adında bir dosya oluşturup aşağıdakileri kendi değerlerinizle doldurun. **`.env` repoya yüklenmez** (`.gitignore` engeller); şifreleri WhatsApp grubunda değil, birbirinize özel mesajla paylaşın.

```
POSTGRES_USER=careerai
POSTGRES_PASSWORD=degistir-bunu
POSTGRES_DB=careerai
DATABASE_URL=postgresql+psycopg://careerai:degistir-bunu@localhost:5432/careerai
REDIS_URL=redis://localhost:6379/0
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
JWT_SECRET=uzun-rastgele-bir-deger
YOUTUBE_API_KEY=
```

Servisler:

| Servis | Adres |
|---|---|
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| Ollama | `localhost:11434` |

## Klasörler

| Klasör | Sahibi | İçerik |
|---|---|---|
| `contracts/` | Ortak | Modüller arası veri formatları ve API listesi |
| `scraper/` | Ataberk | İlan toplama ve veri hazırlama |
| `infra/` | Ataberk | Sunucu, deploy, izleme, yedekleme |
| `ai/` | Burak | CV analizi ve öneri motoru |
| `mobile/` | Burak | Mobil uygulama |
| `backend/` | Anıl (db modelleri: Ataberk) | FastAPI |
| `web/` | Anıl | Web ve Electron arayüzü |
| `docs/` | Ortak | Kararlar ve dokümanlar |

## Çalışma şekli

1. Her gün işe başlamadan: `git checkout main && git pull`
2. Yeni iş için branch aç: `git checkout -b isim/kisa-aciklama`
3. Sadece kendi klasörünüzde çalışın. Başka klasörde değişiklik gerekiyorsa sahibine haber verin.
4. İş bitince push edip PR açın; bir kişi inceleyip onaylasın.
5. `contracts/` değişiklikleri için üç kişinin de onayı gerekir.

Kurallar ve Claude talimatları: [CLAUDE.md](CLAUDE.md)
