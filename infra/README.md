# infra/ — Sahibi: Ataberk

Production PC kurulumu, Docker, Cloudflare Tunnel, CI/CD (GitHub Actions), izleme, yedekleme ve deploy scriptleri.

VPS yoktur: production Ataberk'in PC'sinde çalışır ve alan adına Cloudflare Tunnel ile bağlanır (`docs/kararlar.md` #30). PC hazırlığı ve kontrol listesi: [`pc/README.md`](pc/README.md).

- `pc/`: production PC'si: kurulum listesi (`README.md`), compose ve deploy (`deploy.md`, T-009, T-035, T-036)
- `ci.md`: CI işleri, `main` koruması, imaj üretimi
