"""Veri setini doğrular ve T-019 kabul kriterlerine göre ilerlemeyi gösterir.

Kullanım:
    python ai/eval/scripts/check_labels.py [--dataset DIR] [--skills FILE]

Hata varsa çıkış kodu 1'dir.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _common import (
    DEFAULT_DATASET,
    DEFAULT_SKILLS,
    EXPERIENCE,
    Report,
    assignment,
    load_gold,
    load_labels,
    load_manifest,
    load_skill_names,
    use_utf8_stdout,
)

# T-019 kabul kriteri (docs/gorevler/burak.md)
TARGET_TOTAL = 50
TARGET_PER_LANGUAGE = 25
TARGET_ROLES = 10
TARGET_PER_ROLE = 5
TARGET_SCANNED = 5
TARGET_DOUBLE = 20
# Çift etiketlenen alt kümenin dağılımı
DOUBLE_MIN_PER_LANGUAGE = 8
DOUBLE_MIN_MULTI_COLUMN = 6
DOUBLE_MIN_SCANNED = 2


def main(argv: list[str] | None = None) -> int:
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--skills", type=Path, default=DEFAULT_SKILLS)
    args = parser.parse_args(argv)

    report = Report()
    skill_names = load_skill_names(args.skills)
    manifest = load_manifest(args.dataset, report)
    labels = load_labels(args.dataset, skill_names, report)
    gold = load_gold(args.dataset, skill_names, report)

    for cv_id in sorted(set(labels) | set(gold)):
        if cv_id not in manifest:
            report.error(f"{cv_id}: etiketi var ama manifest.csv'de yok")
    for cv_id, by_annotator in labels.items():
        row = manifest.get(cv_id)
        if row is None:
            continue
        (first, second), _ = assignment(cv_id)
        expected = {first, second} if row["double"] == "true" else {first}
        unexpected = set(by_annotator) - expected
        if unexpected:
            report.warn(
                f"{cv_id}: atama tablosuna göre etiketleyici(ler) {', '.join(sorted(expected))}; "
                f"fazladan: {', '.join(sorted(unexpected))}"
            )
        if row["double"] == "false" and len(by_annotator) > 1:
            report.warn(f"{cv_id}: çift etiket için seçilmemiş ama {len(by_annotator)} etiketi var")

    unknown = Counter(
        item["skill"]
        for source in [*(s for d in labels.values() for s in d.values()), *gold.values()]
        for item in source
        if item["skill"].startswith("?")
    )

    print_progress(manifest, labels, gold)
    if unknown:
        print("\nListede olmayan yetkinlikler (? ile işaretli) — listeye eklenmeli mi?")
        for name, count in unknown.most_common():
            print(f"  {count:3d} × {name}")
    for w in report.warnings:
        print(f"UYARI: {w}")
    for e in report.errors:
        print(f"HATA: {e}")
    print(f"\n{len(report.errors)} hata, {len(report.warnings)} uyarı.")
    return 1 if report.errors else 0


def print_progress(
    manifest: dict[str, dict[str, str]], labels: dict[str, dict[str, list[Any]]], gold: dict[str, list[Any]]
) -> None:
    rows = list(manifest.values())
    total = len(rows)
    langs = Counter(r["language"] for r in rows)
    roles = Counter(r["target_role"] for r in rows)
    layouts = Counter(r["layout"] for r in rows)
    experience = Counter(r["experience"] for r in rows)
    scanned = sum(r["scanned"] == "true" for r in rows)
    labeled = sum(len(labels.get(cv_id, {})) >= 1 for cv_id in manifest)
    gold_count = sum(cv_id in gold for cv_id in manifest)

    double = [r for r in rows if r["double"] == "true"]
    double_langs = Counter(r["language"] for r in double)
    double_multi = sum(r["layout"] == "multi_column" for r in double)
    double_scanned = sum(r["scanned"] == "true" for r in double)
    double_exp = {r["experience"] for r in double}
    double_done = sum(len(labels.get(r["cv_id"], {})) >= 2 for r in double)

    def mark(ok: bool) -> str:
        return "✓" if ok else "✗"

    full_roles = sum(n >= TARGET_PER_ROLE for n in roles.values())
    print("T-019 kabul kriteri (sentetik set)")
    print(f"  {mark(total >= TARGET_TOTAL)} CV sayısı: {total}/{TARGET_TOTAL}")
    print(
        f"  {mark(min(langs['tr'], langs['en']) >= TARGET_PER_LANGUAGE)} Dil: "
        f"TR {langs['tr']}/{TARGET_PER_LANGUAGE}, EN {langs['en']}/{TARGET_PER_LANGUAGE}"
    )
    print(
        f"  {mark(full_roles >= TARGET_ROLES)} Pozisyon: {full_roles}/{TARGET_ROLES} pozisyonda ≥ {TARGET_PER_ROLE} CV "
        f"({len(roles)} farklı pozisyon)"
    )
    print(f"  {mark(layouts['multi_column'] > 0 and layouts['single_column'] > 0)} Düzen: " + _fmt(layouts))
    print(f"  {mark(scanned >= TARGET_SCANNED)} Taranmış: {scanned}/{TARGET_SCANNED}")
    print(f"  {mark(all(experience[e] > 0 for e in EXPERIENCE))} Deneyim: " + _fmt(experience))
    print(f"  {mark(total > 0 and labeled == total)} En az 1 kişi etiketledi: {labeled}/{total}")
    print(
        f"  {mark(len(double) >= TARGET_DOUBLE)} Çift etiket için seçilen: {len(double)}/{TARGET_DOUBLE} "
        f"(TR {double_langs['tr']}, EN {double_langs['en']}, çok sütun {double_multi}, taranmış {double_scanned})"
    )
    balanced = (
        min(double_langs["tr"], double_langs["en"]) >= DOUBLE_MIN_PER_LANGUAGE
        and double_multi >= DOUBLE_MIN_MULTI_COLUMN
        and double_scanned >= DOUBLE_MIN_SCANNED
        and double_exp >= set(EXPERIENCE)
    )
    print(
        f"  {mark(balanced)} Çift etiketli alt küme dengeli: ≥ {DOUBLE_MIN_PER_LANGUAGE} TR + "
        f"{DOUBLE_MIN_PER_LANGUAGE} EN, ≥ {DOUBLE_MIN_MULTI_COLUMN} çok sütun, ≥ {DOUBLE_MIN_SCANNED} taranmış, "
        "3 deneyim düzeyi"
    )
    print(f"  {mark(len(double) > 0 and double_done == len(double))} 2 kişi etiketledi: {double_done}/{len(double)}")
    print(f"  {mark(total > 0 and gold_count == total)} Gold (anlaşmazlık çözülmüş): {gold_count}/{total}")
    print("  · Etiketleyiciler arası F1 ≥ 0,85: agreement.py ile ölçülür.")


def _fmt(counter: Counter[str]) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted(counter.items())) or "—"


if __name__ == "__main__":
    sys.exit(main())
