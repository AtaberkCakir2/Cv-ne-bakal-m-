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
    Report,
    assignment,
    load_gold,
    load_labels,
    load_manifest,
    load_skill_names,
    use_utf8_stdout,
)

TARGET_TOTAL = 50
TARGET_SCANNED = 5


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
        expected, _ = assignment(cv_id)
        unexpected = set(by_annotator) - set(expected)
        if unexpected:
            report.warn(
                f"{cv_id}: atama tablosuna göre etiketleyiciler {', '.join(expected)}; "
                f"fazladan: {', '.join(sorted(unexpected))}"
            )

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
    rows = manifest.values()
    total = len(manifest)
    real = sum(r["source"] == "real" for r in rows)
    langs = Counter(r["language"] for r in rows)
    layouts = Counter(r["layout"] for r in rows)
    scanned = sum(r["scanned"] == "true" for r in rows)
    double = sum(len(labels.get(cv_id, {})) >= 2 for cv_id in manifest)
    gold_count = sum(cv_id in gold for cv_id in manifest)

    def mark(ok: bool) -> str:
        return "✓" if ok else "✗"

    print("T-019 kabul kriteri")
    print(f"  {mark(total >= TARGET_TOTAL)} CV sayısı: {total}/{TARGET_TOTAL} (gerçek {real}, sentetik {total - real})")
    print(f"  {mark(langs['tr'] > 0 and langs['en'] > 0)} Dil: TR {langs['tr']}, EN {langs['en']}")
    print(f"  {mark(len(layouts) >= 3)} Format: " + ", ".join(f"{k} {v}" for k, v in sorted(layouts.items())))
    print(f"  {mark(scanned >= TARGET_SCANNED)} Taranmış: {scanned}/{TARGET_SCANNED}")
    print(f"  {mark(total > 0 and double == total)} 2 kişi etiketledi: {double}/{total}")
    print(f"  {mark(total > 0 and gold_count == total)} Anlaşmazlık çözüldü (gold): {gold_count}/{total}")
    print("  · Gerçek CV izinleri: consent_id dolu olmalı (yukarıdaki hatalara bakın); imzalı formlar repo dışında.")


if __name__ == "__main__":
    sys.exit(main())
