"""OpenAPI tanımını yazar (T-080): `docs/api/openapi.json` ve web tipleri için `web/src/api/openapi.json`.

Kullanım (backend/ klasöründe):
    python scripts/export_openapi.py           # iki dosyayı yazar
    python scripts/export_openapi.py --check   # dosyalar eskiyse 1 ile çıkar (testler de denetler)

Sunucu çalıştırmaya gerek yoktur; tanım uygulamadan doğrudan üretilir. Endpoint değiştiğinde çalıştırın, sonra
web/ içinde `npm run gen:api` ile tipleri yenileyin ve üç dosyayı birlikte commit'leyin.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
TARGETS = (REPO / "docs" / "api" / "openapi.json", REPO / "web" / "src" / "api" / "openapi.json")

sys.path.insert(0, str(BACKEND))  # app paketi


def build_schema() -> dict[str, Any]:
    from app.core.config import Settings
    from app.main import create_app

    # .env okunmaz: çıktı kimin bilgisayarında üretilirse üretilsin aynı olmalı.
    settings = Settings(_env_file=None, environment="test", app_name="CareerAI API", api_prefix="/api/v1")
    return create_app(settings).openapi()


def render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, ensure_ascii=False, indent=2) + "\n"


def is_current(target: Path, text: str) -> bool:
    # Windows'ta Git dosyayı CRLF ile çıkarabilir; satır sonu farkı "eski" sayılmaz.
    return target.exists() and target.read_text(encoding="utf-8").replace("\r\n", "\n") == text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="yazma, sadece güncel mi bak")
    args = parser.parse_args()
    text = render(build_schema())
    stale = [t for t in TARGETS if not is_current(t, text)]
    if args.check:
        for t in stale:
            print(f"Güncel değil: {t.relative_to(REPO)} (python scripts/export_openapi.py)")
        return 1 if stale else 0
    for t in TARGETS:
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(text, encoding="utf-8", newline="\n")
        print(f"Yazıldı: {t.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
