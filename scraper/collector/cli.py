"""Komut satırı. Veritabanı adresi repo kökündeki .env'deki DATABASE_URL'den okunur.

python -m collector import hn --months 6
python -m collector import himalayas --pages 5
python -m collector import remoteok
python -m collector import remotive
python -m collector import emscad --csv data/fake_job_postings.csv [--active]
python -m collector stats
python -m collector seed-taxonomy
python -m collector export-taxonomy --out taxonomy.json
"""

import argparse
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from app.db.session import get_sessionmaker

from collector import esco, taxonomy
from collector.http import PoliteClient
from collector.posting import Posting, SourceInfo
from collector.sources import emscad, himalayas, hn, remoteok, remotive
from collector.store import run_import, source_counts


def _api(info: SourceInfo, fetch: Callable[[PoliteClient], Iterable[Posting]]) -> tuple[SourceInfo, Iterable[Posting]]:
    return info, fetch(PoliteClient(delay_s=info.rate_limit_sec))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="collector", description="CareerAI ilan toplayıcı")
    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import", help="Bir kaynaktan ilanları içe aktar")
    src = imp.add_subparsers(dest="source", required=True)
    src.add_parser("hn", help="Hacker News 'Who is hiring?'").add_argument("--months", type=int, default=6)
    src.add_parser("himalayas", help="Himalayas yazılım aramaları").add_argument("--pages", type=int, default=5)
    src.add_parser("remoteok", help="Remote OK")
    src.add_parser("remotive", help="Remotive (günde en fazla birkaç kez)")
    em = src.add_parser("emscad", help="EMSCAD veri seti (yerel CSV)")
    em.add_argument("--csv", type=Path, required=True)
    em.add_argument("--active", action="store_true", help="İstatistiklere dahil et (sadece yedek plan için)")

    sub.add_parser("stats", help="Kaynak başına ilan sayıları")
    sub.add_parser("seed-taxonomy", help="taxonomy/*.csv → skills ve roles tabloları (T-017)")
    exp = sub.add_parser("export-taxonomy", help="Yetkinlikleri JSON'a yaz (ai/eval biçimi)")
    exp.add_argument("--out", type=Path, required=True)
    esc = sub.add_parser("map-esco", help="ESCO skills_en.csv ile taxonomy/skills.csv'ye esco_uri yaz")
    esc.add_argument("--csv", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "export-taxonomy":
        skills = taxonomy.load_skills()
        taxonomy.export_json(skills, args.out)
        print(f"{len(skills)} yetkinlik yazıldı: {args.out}")
        return 0

    if args.command == "map-esco":
        before = taxonomy.load_skills()
        after = esco.map_skills(before, esco.load_esco_index(args.csv))
        esco.write_skills(after)
        added = sum(1 for b, a in zip(before, after, strict=True) if a.esco_uri and not b.esco_uri)
        print(f"{added} yetkinliğe ESCO URI eklendi; toplam eşli: {sum(1 for a in after if a.esco_uri)}/{len(after)}")
        return 0

    session_factory = get_sessionmaker()

    if args.command == "seed-taxonomy":
        with session_factory() as session:
            r = taxonomy.seed(session, taxonomy.load_skills(), taxonomy.load_roles())
        print(
            f"yetkinlik: +{r.skills_added} ~{r.skills_updated} pasif {r.skills_deactivated} | "
            f"pozisyon: +{r.roles_added} ~{r.roles_updated} pasif {r.roles_deactivated}"
        )
        return 0

    if args.command == "stats":
        with session_factory() as session:
            rows = source_counts(session)
        print(f"{'kaynak':<16}{'aktif':>8}{'toplam':>8}")
        for name, active, total in rows:
            print(f"{name:<16}{active:>8}{total:>8}")
        print(f"{'TOPLAM':<16}{sum(r[1] for r in rows):>8}{sum(r[2] for r in rows):>8}")
        return 0

    active = True
    if args.source == "hn":
        info, postings = _api(hn.SOURCE, lambda c: hn.fetch(c, months=args.months))
    elif args.source == "himalayas":
        info, postings = _api(himalayas.SOURCE, lambda c: himalayas.fetch(c, pages_per_query=args.pages))
    elif args.source == "remoteok":
        info, postings = _api(remoteok.SOURCE, remoteok.fetch)
    elif args.source == "remotive":
        info, postings = _api(remotive.SOURCE, remotive.fetch)
    else:
        info, postings, active = emscad.SOURCE, emscad.fetch(args.csv), args.active

    with session_factory() as session:
        result = run_import(session, info, postings, active=active)
    print(f"{info.name}: {result.fetched} ilan okundu, {result.inserted} eklendi, {result.duplicates} tekrar atlandı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
