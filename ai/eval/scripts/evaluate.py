"""Model değerlendirmesi (T-055): üretimdeki çıkarım zinciri gold etiketlere karşı.

Her CV için `pipeline.analyze_cv`'nin ilk üç adımı aynen çalışır: PDF → `parsing.extract_text` → `pii.mask`
(BERTurk ad tespitiyle, kuruluysa) → `extraction.llm.extract_skills_v2` (v1 sözlük + yerel Ollama). Eşleştirme ve
öneri adımları veritabanı ister; öneri alakalılığı ayrıca 3 değerlendiricinin puanıyla ölçülür (report.md).

Kullanım (Ollama çalışırken, ai/ klasöründe):
    python eval/scripts/evaluate.py run --tag 2026-11-27
    python eval/scripts/evaluate.py report --tag 2026-11-27

`run` sonuçları eval/results/<tag>.jsonl dosyasına yazar. Dosyada CV metni yoktur; sadece çıkarılan yetkinlik
adları, seviyeler ve süreler tutulur (CLAUDE.md kural 5; veri zaten sentetik, karar #20).
`report` gold'a göre kesinlik/duyarlılık/F1, seviye doğruluğu ve gecikmeyi Markdown tablosu olarak basar.

Taranmış CV'ler: OCR (T-029) gelene kadar üretimde NO_TEXT_FOUND döner; burada da yetkinlik çıkarılmaz ve
duyarlılığa 0 olarak yansır. Rapor ayrıca sadece metinli PDF'lerin sonucunu verir.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import DEFAULT_DATASET, EVAL_DIR, use_utf8_stdout  # noqa: E402

RESULTS = EVAL_DIR / "results"
F1_TARGET = 0.80


# --- Puanlama (Ollama gerektirmez) ---------------------------------------------------------------------------------


def key(name: str) -> str:
    """Karşılaştırma anahtarı: gold'daki taksonomi dışı işareti (?) ve büyük/küçük harf farkı yok sayılır."""
    return " ".join(name.removeprefix("?").split()).casefold()


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def add(self, other: Counts) -> None:
        self.tp += other.tp
        self.fp += other.fp
        self.fn += other.fn

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass
class CvScore:
    counts: Counts
    level_pairs: list[tuple[str, str]]  # (gold, tahmin) doğru bulunan yetkinlikler için
    fp_names: list[str]
    fn_names: list[str]


def score_cv(pred: list[dict[str, Any]], gold: list[dict[str, Any]], *, in_taxonomy: bool = False) -> CvScore:
    """`in_taxonomy`: sadece taksonomideki yetkinlikler (gold'da ? olmayan, tahminde verified)."""
    if in_taxonomy:
        pred = [p for p in pred if p.get("verified")]
        gold = [g for g in gold if not g["skill"].startswith("?")]
    p = {key(s["skill"]): s for s in pred}
    g = {key(s["skill"]): s for s in gold}
    both = p.keys() & g.keys()
    return CvScore(
        Counts(len(both), len(p.keys() - g.keys()), len(g.keys() - p.keys())),
        [(g[k]["level"], p[k]["level"]) for k in sorted(both)],
        sorted(p[k]["skill"] for k in p.keys() - g.keys()),
        sorted(g[k]["skill"] for k in g.keys() - p.keys()),
    )


def percentile(values: Iterable[float], q: float) -> float:
    """En yakın sıra yöntemi (nearest-rank): p95 gerçekten ölçülmüş bir değerdir."""
    xs = sorted(values)
    if not xs:
        return math.nan
    return xs[max(0, math.ceil(q / 100 * len(xs)) - 1)]


def level_accuracy(pairs: list[tuple[str, str]]) -> tuple[float, int]:
    """Gold seviyesi bilinen (unknown olmayan) doğru yetkinliklerde seviyenin aynı olma oranı."""
    known = [(g, p) for g, p in pairs if g != "unknown"]
    if not known:
        return math.nan, 0
    return sum(g == p for g, p in known) / len(known), len(known)


# --- Çalıştırma ----------------------------------------------------------------------------------------------------


def load_manifest(dataset: Path) -> list[dict[str, str]]:
    with (dataset / "manifest.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_gold(dataset: Path) -> dict[str, dict[str, Any]]:
    gold = {}
    for path in sorted((dataset / "gold").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        gold[data["cv_id"]] = data
    return gold


def analyze(
    pdf: bytes,
    *,
    model: str | None,
    prompt: str | None = None,
    detector: Any = None,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """`pipeline.analyze_cv` 1-3. adımları; ham metin bu fonksiyondan çıkmaz."""
    from extraction.llm import extract_skills_v2
    from parsing import extract_text
    from pii import mask
    from pipeline import guess_lang

    t0 = clock()
    parsed = extract_text(pdf)
    t1 = clock()
    if parsed.needs_ocr:
        return {"status": "needs_ocr", "parse_s": round(t1 - t0, 2), "skills": []}
    lang = guess_lang(parsed.text)
    masked = mask(parsed.text, lang, detector=detector)
    del parsed
    t2 = clock()
    from prompts import get_prompt

    result = extract_skills_v2(masked.text, lang, model=model, prompt=get_prompt("skill_extraction", prompt))
    t3 = clock()
    return {
        "status": "ok" if result.llm_error is None else "llm_fallback",
        "lang": lang,
        "llm_error": result.llm_error,
        "model": result.model,
        "parse_s": round(t1 - t0, 2),
        "mask_s": round(t2 - t1, 2),
        "extract_s": round(t3 - t2, 2),
        "total_s": round(t3 - t0, 2),
        "skills": [
            {"skill": s.skill, "level": s.level, "years": s.years, "verified": s.verified, "source": s.source}
            for s in result.skills
        ],
    }


def run(dataset: Path, tag: str, *, model: str | None, prompt: str | None = None, limit: int | None, ner: bool) -> Path:
    from pii.ner import default_detector

    detector = default_detector() if ner else None
    out = RESULTS / f"{tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = (
        {json.loads(line)["cv_id"] for line in out.read_text(encoding="utf-8").splitlines()} if out.exists() else set()
    )
    rows = [r for r in load_manifest(dataset) if r["cv_id"] not in done][:limit]
    for i, row in enumerate(rows, 1):
        pdf = dataset / "synthetic" / f"{row['cv_id']}.pdf"
        record = {
            "cv_id": row["cv_id"],
            "ner": detector is not None,
            **analyze(pdf.read_bytes(), model=model, prompt=prompt, detector=detector),
        }
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(
            f"[{i}/{len(rows)}] {row['cv_id']} {record['status']} {record.get('total_s', '-')} sn, "
            f"{len(record['skills'])} yetkinlik",
            flush=True,
        )
    return out


# --- Rapor ---------------------------------------------------------------------------------------------------------


def _fmt(x: float, digits: int = 2) -> str:
    return "–" if math.isnan(x) else f"{x:.{digits}f}".replace(".", ",")


def _row(name: str, n: int, c: Counts) -> str:
    return f"| {name} | {n} | {_fmt(c.precision)} | {_fmt(c.recall)} | **{_fmt(c.f1)}** | {c.tp} | {c.fp} | {c.fn} |"


def report(dataset: Path, tag: str, top: int = 15) -> str:
    records = {
        r["cv_id"]: r
        for r in (json.loads(line) for line in (RESULTS / f"{tag}.jsonl").read_text(encoding="utf-8").splitlines())
    }
    gold = load_gold(dataset)
    manifest = {r["cv_id"]: r for r in load_manifest(dataset)}
    ids = sorted(records.keys() & gold.keys())
    scores = {cv: score_cv(records[cv]["skills"], gold[cv]["skills"]) for cv in ids}
    tax = {cv: score_cv(records[cv]["skills"], gold[cv]["skills"], in_taxonomy=True) for cv in ids}
    text_ids = [cv for cv in ids if records[cv]["status"] != "needs_ocr"]

    def total(group: Iterable[str], source: dict[str, CvScore] = scores) -> Counts:
        c = Counts()
        for cv in group:
            c.add(source[cv].counts)
        return c

    lines = [
        f"Sonuç dosyası: `eval/results/{tag}.jsonl` · CV: {len(ids)} · gold hakemi: "
        + ", ".join(f"{k} {v}" for k, v in Counter(gold[cv].get("adjudicator") for cv in ids).most_common()),
        "",
        "| Kapsam | CV | Kesinlik | Duyarlılık | F1 | Doğru | Fazla | Eksik |",
        "|---|---|---|---|---|---|---|---|",
        _row("Tüm CV'ler (taranmış = boş)", len(ids), total(ids)),
        _row("Metinli PDF'ler", len(text_ids), total(text_ids)),
        _row("Metinli, sadece taksonomi içi", len(text_ids), total(text_ids, tax)),
        "",
        f"Hedef F1 ≥ {_fmt(F1_TARGET)} (kabul kriteri). Mikro ortalama: tüm yetkinlikler tek havuzda sayılır.",
        "",
        "**Kırılımlar (metinli PDF'ler):**",
        "",
        "| Grup | CV | Kesinlik | Duyarlılık | F1 | Doğru | Fazla | Eksik |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for field in ("language", "layout", "experience"):
        values = sorted({manifest[cv][field] for cv in text_ids})
        for v in values:
            group = [cv for cv in text_ids if manifest[cv][field] == v]
            lines.append(_row(f"{field} = {v}", len(group), total(group)))

    pairs = [p for cv in text_ids for p in scores[cv].level_pairs]
    acc, n_known = level_accuracy(pairs)
    pred_unknown = sum(g != "unknown" and p == "unknown" for g, p in pairs)
    lines += [
        "",
        f"**Seviye:** doğru bulunan {len(pairs)} yetkinliğin {n_known}'inde gold seviyesi belli; bunların "
        f"%{_fmt(acc * 100, 0)}'inde model aynı seviyeyi verdi. Model {pred_unknown}'inde 'unknown' dedi.",
        "",
        "| Gold \\ Model | " + " | ".join(("beginner", "intermediate", "advanced", "unknown")) + " |",
        "|---|---|---|---|---|",
    ]
    matrix = Counter(pairs)
    for g in ("beginner", "intermediate", "advanced", "unknown"):
        cells = [str(matrix[(g, p)]) for p in ("beginner", "intermediate", "advanced", "unknown")]
        lines.append(f"| {g} | " + " | ".join(cells) + " |")

    ok = [records[cv] for cv in text_ids]
    lines += [
        "",
        "**Gecikme (sn, metinli PDF'ler; analiz işçisinin sınırı 180 sn, çıkarımın payı 90 sn):**",
        "",
        "| Adım | p50 | p95 | en fazla |",
        "|---|---|---|---|",
    ]
    for step, label in (
        ("parse_s", "PDF → metin"),
        ("mask_s", "Maskeleme"),
        ("extract_s", "Çıkarım (v1 + LLM)"),
        ("total_s", "Toplam (1–3)"),
    ):
        vals = [r[step] for r in ok if step in r]
        lines.append(
            f"| {label} | {_fmt(percentile(vals, 50), 1)} | {_fmt(percentile(vals, 95), 1)} | "
            f"{_fmt(max(vals, default=math.nan), 1)} |"
        )
    fallbacks = Counter(r.get("llm_error") for r in ok if r["status"] == "llm_fallback")
    if fallbacks:
        lines.append("")
        lines.append("LLM düşüp v1'e dönülen CV: " + ", ".join(f"{k} × {v}" for k, v in fallbacks.items()))

    fn = Counter(n for cv in text_ids for n in scores[cv].fn_names)
    fp = Counter(n for cv in text_ids for n in scores[cv].fp_names)
    lines += [
        "",
        "**En sık kaçırılan (eksik):** " + ", ".join(f"{n} ({c})" for n, c in fn.most_common(top)),
        "",
        "**En sık fazla bulunan:** " + ", ".join(f"{n} ({c})" for n, c in fp.most_common(top)),
        "",
        "**CV bazında (F1 en düşük 10):**",
        "",
        "| CV | Durum | F1 | Eksik | Fazla |",
        "|---|---|---|---|---|",
    ]
    for cv in sorted(ids, key=lambda c: (scores[c].counts.f1, c))[:10]:
        s = scores[cv]
        lines.append(
            f"| {cv} | {records[cv]['status']} | {_fmt(s.counts.f1)} | {', '.join(s.fn_names[:6])} | "
            f"{', '.join(s.fp_names[:6])} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="CV'leri zincirden geçirir (Ollama gerekir); yarıda kalırsa kaldığı yerden sürer")
    r.add_argument("--tag", required=True)
    r.add_argument("--model", help="varsayılan: OLLAMA_MODEL veya extraction.llm.DEFAULT_MODEL")
    r.add_argument("--prompt", help="skill_extraction sürümü (ör. v3); varsayılan: prompts.CURRENT")
    r.add_argument("--limit", type=int)
    r.add_argument("--no-ner", action="store_true", help="ad tespitinde BERTurk'ü kullanma (sadece kurallar)")
    p = sub.add_parser("report", help="sonuç dosyasını gold'a göre puanlar")
    p.add_argument("--tag", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "run":
        print(run(args.dataset, args.tag, model=args.model, prompt=args.prompt, limit=args.limit, ner=not args.no_ner))
    else:
        print(report(args.dataset, args.tag), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
