"""İki etiketleyici arasındaki uyumu ölçer ve anlaşmazlıkları listeler.

Kullanım:
    python ai/eval/scripts/agreement.py [--dataset DIR] [--skills FILE] [--write-gold]

--write-gold: gold/ dosyası olmayan her etiketli CV için gold yazar. 2 etiketi olan CV'de
anlaşılan yetkinlikler 'skills'e, anlaşmazlıklar '_karar_bekleyen'e girer; hakem sadece
'_karar_bekleyen'i çözer. Tek etiketli CV'de etiket olduğu gibi kopyalanır; ama sadece manifest'te
double=false ise (double=true olan CV ikinci etiketi bekler). Var olan gold dosyalarına dokunulmaz.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _common import (
    AI_ANNOTATOR,
    DEFAULT_DATASET,
    DEFAULT_SKILLS,
    LEVELS,
    PENDING_KEY,
    Report,
    assignment,
    load_labels,
    load_manifest,
    load_skill_names,
    use_utf8_stdout,
)

LOW_F1 = 0.85


@dataclass
class PairResult:
    cv_id: str
    a: str
    b: str
    only_a: list[str]
    only_b: list[str]
    level_pairs: list[tuple[str, str, str]]  # (yetkinlik, a seviyesi, b seviyesi)

    @property
    def both(self) -> int:
        return len(self.level_pairs)

    @property
    def f1(self) -> float:
        denom = 2 * self.both + len(self.only_a) + len(self.only_b)
        return 1.0 if denom == 0 else 2 * self.both / denom

    @property
    def level_diffs(self) -> list[tuple[str, str, str]]:
        return [p for p in self.level_pairs if p[1] != p[2]]


def compare(cv_id: str, a: str, skills_a: list[dict[str, Any]], b: str, skills_b: list[dict[str, Any]]) -> PairResult:
    by_a = {s["skill"]: s for s in skills_a}
    by_b = {s["skill"]: s for s in skills_b}
    common = sorted(by_a.keys() & by_b.keys())
    return PairResult(
        cv_id=cv_id,
        a=a,
        b=b,
        only_a=sorted(by_a.keys() - by_b.keys()),
        only_b=sorted(by_b.keys() - by_a.keys()),
        level_pairs=[(k, by_a[k]["level"], by_b[k]["level"]) for k in common],
    )


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    n = len(pairs)
    if n == 0:
        return None
    observed = sum(x == y for x, y in pairs) / n
    count_a = Counter(x for x, _ in pairs)
    count_b = Counter(y for _, y in pairs)
    expected = sum(count_a[lv] * count_b[lv] for lv in LEVELS) / (n * n)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def pick_pair(by_annotator: dict[str, list[dict[str, Any]]], cv_id: str) -> tuple[str, str] | None:
    """Atama tablosundaki ikiliyi tercih eder; yoksa ilk iki etiketleyiciyi alır."""
    expected, _ = assignment(cv_id)
    if all(name in by_annotator for name in expected):
        return expected
    names = sorted(by_annotator)
    return (names[0], names[1]) if len(names) >= 2 else None


def gold_draft(result: PairResult, skills_a: list[dict[str, Any]], skills_b: list[dict[str, Any]]) -> dict[str, Any]:
    by_a = {s["skill"]: s for s in skills_a}
    by_b = {s["skill"]: s for s in skills_b}
    agreed: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    for skill, lv_a, lv_b in result.level_pairs:
        if lv_a == lv_b:
            years = by_a[skill].get("years") if by_a[skill].get("years") == by_b[skill].get("years") else None
            agreed.append({"skill": skill, "level": lv_a, "years": years})
        else:
            pending.append({"skill": skill, "sorun": "seviye farklı", result.a: lv_a, result.b: lv_b})
    for skill in result.only_a:
        pending.append(
            {"skill": skill, "sorun": f"sadece {result.a} buldu", result.a: by_a[skill]["level"], result.b: None}
        )
    for skill in result.only_b:
        pending.append(
            {"skill": skill, "sorun": f"sadece {result.b} buldu", result.a: None, result.b: by_b[skill]["level"]}
        )
    _, adjudicator = assignment(result.cv_id)
    return {
        "cv_id": result.cv_id,
        "adjudicator": adjudicator,
        "skills": agreed,
        PENDING_KEY: pending,
        "notes": "",
    }


def write_single_gold(dataset: Path, cv_id: str, by_annotator: dict[str, list[dict[str, Any]]]) -> None:
    """Tek etiketli CV: etiket gold'a olduğu gibi kopyalanır (çift etiket sadece seçilen 20 CV'de)."""
    path = dataset / "gold" / f"{cv_id}.json"
    if path.exists():
        return
    ((annotator, skills),) = by_annotator.items()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"cv_id": cv_id, "adjudicator": annotator, "skills": skills, "notes": "tek etiketleyici"}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{cv_id}: tek etiketli, gold'a kopyalandı: {path}")


def main(argv: list[str] | None = None) -> int:
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--skills", type=Path, default=DEFAULT_SKILLS)
    parser.add_argument("--write-gold", action="store_true")
    args = parser.parse_args(argv)

    report = Report()
    labels = load_labels(args.dataset, load_skill_names(args.skills), report)
    manifest = load_manifest(args.dataset, report)
    for e in report.errors:
        print(f"HATA: {e}")
    if report.errors:
        print("Önce check_labels.py hatalarını düzeltin.")
        return 1

    results: list[PairResult] = []
    for cv_id, by_annotator in sorted(labels.items()):
        pair = pick_pair(by_annotator, cv_id)
        if pair is None:
            if args.write_gold and len(by_annotator) == 1:
                double = manifest.get(cv_id, {}).get("double")
                # Karar #40: sadece Claude etiketi varsa CV çift etiketli olsa da gold'a kopyalanır.
                if double == "false" or (double == "true" and set(by_annotator) == {AI_ANNOTATOR}):
                    write_single_gold(args.dataset, cv_id, by_annotator)
                elif double == "true":
                    print(f"{cv_id}: çift etiketli CV, ikinci etiket bekleniyor; gold yazılmadı")
                else:
                    print(f"{cv_id}: manifest'te yok; gold yazılmadı")
            continue
        a, b = pair
        result = compare(cv_id, a, by_annotator[a], b, by_annotator[b])
        results.append(result)

        flag = "  ← düşük" if result.f1 < LOW_F1 else ""
        print(f"\n{cv_id} ({a} × {b}): F1 {result.f1:.2f}, ortak {result.both}{flag}")
        for skill in result.only_a:
            print(f"  - sadece {a}: {skill}")
        for skill in result.only_b:
            print(f"  - sadece {b}: {skill}")
        for skill, lv_a, lv_b in result.level_diffs:
            print(f"  - seviye: {skill} ({a}={lv_a}, {b}={lv_b})")

        if args.write_gold:
            path = args.dataset / "gold" / f"{cv_id}.json"
            if path.exists():
                print(f"  gold zaten var, dokunulmadı: {path}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                draft = gold_draft(result, by_annotator[a], by_annotator[b])
                path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"  gold taslağı yazıldı ({len(draft[PENDING_KEY])} karar bekliyor): {path}")

    if not results:
        print("İki etiketi olan CV yok.")
        return 0

    both = sum(r.both for r in results)
    only = sum(len(r.only_a) + len(r.only_b) for r in results)
    micro_f1 = 2 * both / (2 * both + only) if (2 * both + only) else 1.0
    level_pairs = [(lv_a, lv_b) for r in results for _, lv_a, lv_b in r.level_pairs]
    level_agree = sum(x == y for x, y in level_pairs) / len(level_pairs) if level_pairs else 1.0
    kappa = cohen_kappa(level_pairs)

    print("\n=== Toplam ===")
    print(f"CV: {len(results)}")
    print(f"Yetkinlik micro-F1: {micro_f1:.3f}" + ("  ← kılavuzu gözden geçirin" if micro_f1 < LOW_F1 else ""))
    print(f"Seviye uyumu: {level_agree:.3f}, Cohen's kappa: " + ("—" if kappa is None else f"{kappa:.3f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
