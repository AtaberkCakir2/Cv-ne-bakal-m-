"""Yerel LLM benchmark'ı (T-018): Ollama modellerinin Türkçe CV'den yetkinlik çıkarımı.

Her CV için: PDF → metin (parsing) → kişisel veri maskeleme (pii) → Ollama → JSON → taksonomiye eşleme.
Ölçülenler: JSON uyumu, referansa göre kesinlik/duyarlılık/F1, taksonomi dışı ad oranı, token/sn, süre, bellek.

Kullanım (Ollama çalışırken, ai/ klasöründe):
    python eval/scripts/benchmark_llm.py run --models llama3.1:8b gemma2:9b qwen2.5:7b --device gpu --mode schema
    python eval/scripts/benchmark_llm.py run --models llama3.1:8b --device cpu --mode schema
    python eval/scripts/benchmark_llm.py report

Sonuçlar eval/benchmark/results/*.jsonl dosyalarına eklenir; `report` hepsini tabloya döker. Sadece sentetik CV
kullanılır (karar #20); model çıktısında CV metni saklanmaz, sadece çıkarılan yetkinlik adları tutulur.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import use_utf8_stdout  # noqa: E402

from parsing import extract_text  # noqa: E402
from pii import mask  # noqa: E402
from prompts import get_prompt  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent.parent
DATASET = EVAL_DIR / "dataset"
BENCH = EVAL_DIR / "benchmark"
RESULTS = BENCH / "results"
REFERENCE = BENCH / "reference_draft.json"
TAXONOMY = EVAL_DIR.parents[1] / "scraper" / "taxonomy" / "skills.csv"
OLLAMA = "http://localhost:11434"
LEVELS = ["beginner", "intermediate", "advanced", "unknown"]

# T-018 ölçümleri bu sürümle yapıldı; karşılaştırılabilir olması için sabit.
SYSTEM_PROMPT = get_prompt("skill_extraction", "v1").text

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "level": {"type": "string", "enum": LEVELS},
                    "years": {"type": ["integer", "null"]},
                },
                "required": ["skill", "level", "years"],
            },
        }
    },
    "required": ["skills"],
}


# --- Veri --------------------------------------------------------------------------------------------------------


def load_aliases(path: Path = TAXONOMY) -> dict[str, str]:
    """Küçük harfli ad / eş anlamlı → taksonomideki standart ad."""
    aliases: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            name = row["canonical_name"]
            aliases[name.lower()] = name
            for syn in row["synonyms"].split("|"):
                if syn.strip():
                    aliases.setdefault(syn.strip().lower(), name)
    return aliases


def _lookup(name: str, aliases: dict[str, str]) -> str | None:
    key = re.sub(r"\s+", " ", name).strip().lower()
    # "Python (ileri)", "React.js", "Express" (→ Express.js) gibi biçimler
    stripped = re.sub(r"\s*\(.*?\)\s*", "", key).strip()
    for cand in (
        key,
        stripped,
        stripped.removesuffix(".js"),
        stripped + ".js",
        stripped.removesuffix(" programlama dili"),
    ):
        if cand in aliases:
            return aliases[cand]
    return None


def normalize(name: str, aliases: dict[str, str]) -> list[str] | None:
    """Model çıktısındaki adı taksonomi adlarına çevirir; "TensorFlow/Keras", "Git & GitHub" ikiye ayrılır."""
    whole = _lookup(name, aliases)
    if whole:
        return [whole]
    parts = [p for p in re.split(r"\s*(?:/|&|,|\+| ve | and )\s*", name) if p.strip()]
    if len(parts) > 1:
        found = [_lookup(p, aliases) for p in parts]
        if all(found):
            return [f for f in found if f]
    return None


def spec_text(spec: dict[str, Any]) -> str:
    """Taranmış CV'ler için (OCR, T-029, henüz yok) spec'teki metin; başlık ve iletişim satırı dahil."""
    out: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)

    walk(spec["header"])
    walk(spec.get("sidebar"))
    walk(spec.get("main"))
    return "\n".join(out)


def load_cvs(language: str = "tr") -> list[tuple[str, str, str]]:
    """(cv_id, maskelenmiş metin, kaynak) listesi. Kaynak: 'pdf' veya 'spec' (taranmış CV, OCR yok)."""
    cvs = []
    with (DATASET / "manifest.csv").open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["language"] == language]
    for row in rows:
        pdf = DATASET / "synthetic" / f"{row['cv_id']}.pdf"
        if not pdf.is_file():
            continue
        result = extract_text(pdf.read_bytes())
        text, source = result.text, "pdf"
        if result.needs_ocr:
            spec = json.loads((DATASET / "cv_specs" / f"{row['cv_id']}.json").read_text(encoding="utf-8"))
            text, source = spec_text(spec), "spec"
        cvs.append((row["cv_id"], mask(text, "tr").text, source))
    return cvs


# --- Ollama ------------------------------------------------------------------------------------------------------


def _post(path: str, body: dict[str, Any], timeout: float = 900) -> dict[str, Any]:
    req = urllib.request.Request(  # noqa: S310 (sabit yerel adres)
        OLLAMA + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (yerel Ollama)
        data: dict[str, Any] = json.loads(resp.read())
    return data


def _get(path: str) -> dict[str, Any]:
    with urllib.request.urlopen(OLLAMA + path, timeout=30) as resp:  # noqa: S310
        data: dict[str, Any] = json.loads(resp.read())
    return data


def chat(model: str, text: str, *, device: str, mode: str) -> dict[str, Any]:
    options: dict[str, Any] = {"temperature": 0.1, "seed": 42, "num_ctx": 8192}
    if device == "cpu":
        options["num_gpu"] = 0
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
        "stream": False,
        "options": options,
        "keep_alive": "10m",
    }
    if mode == "schema":
        body["format"] = SCHEMA
    return _post("/api/chat", body)


def loaded_memory(model: str) -> tuple[int, int]:
    """(toplam bayt, GPU'daki bayt) — Ollama'nın modele ayırdığı bellek."""
    for m in _get("/api/ps").get("models", []):
        if m.get("name") == model or m.get("model") == model:
            return int(m.get("size", 0)), int(m.get("size_vram", 0))
    return 0, 0


def unload(model: str) -> None:
    _post("/api/generate", {"model": model, "keep_alive": 0}, timeout=120)


# --- Değerlendirme -----------------------------------------------------------------------------------------------


def parse_output(content: str) -> tuple[bool, bool, list[dict[str, Any]]]:
    """(saf JSON mu, şemaya uygun mu, yetkinlikler). Kod bloğu (```json) varsa saf sayılmaz ama ayıklanır."""
    raw = content.strip()
    strict = True
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        strict = False
        m = re.search(r"\{.*\}", raw, re.S)
        try:
            data = json.loads(m.group()) if m else None
        except json.JSONDecodeError:
            data = None
    if not isinstance(data, dict) or not isinstance(data.get("skills"), list):
        return False, False, []
    items = data["skills"]
    valid = all(
        isinstance(i, dict)
        and isinstance(i.get("skill"), str)
        and i.get("level") in LEVELS
        and (i.get("years") is None or isinstance(i.get("years"), int))
        for i in items
    )
    return strict, valid, [i for i in items if isinstance(i, dict) and isinstance(i.get("skill"), str)]


def score(pred_names: list[str], ref: set[str], aliases: dict[str, str]) -> dict[str, Any]:
    pred: set[str] = set()
    off_names: set[str] = set()
    off_taxonomy = 0
    for n in pred_names:
        mapped = normalize(n, aliases)
        if mapped is None:
            off_taxonomy += 1
            off_names.add(n)
        else:
            pred.update(mapped)
    tp = len(pred & ref)
    return {
        "tp": tp,
        "fp": len(pred - ref),
        "fn": len(ref - pred),
        "off_taxonomy": off_taxonomy,
        "n_pred": len(pred_names),
        "fp_names": sorted(pred - ref),
        "fn_names": sorted(ref - pred),
        "off_names": sorted(off_names),
    }


def run(models: list[str], device: str, mode: str, tag: str) -> None:
    aliases = load_aliases()
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))["cvs"]
    cvs = load_cvs()
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{tag or 'results'}.jsonl"
    for model in models:
        print(f"== {model} · {device} · {mode} ({len(cvs)} CV)")
        t0 = time.perf_counter()
        chat(model, "Python ve SQL biliyorum.", device=device, mode=mode)  # ısınma: yükleme süresi ayrı ölçülür
        warm_s = time.perf_counter() - t0
        mem_total, mem_vram = loaded_memory(model)
        for cv_id, text, source in cvs:
            t = time.perf_counter()
            resp = chat(model, text, device=device, mode=mode)
            wall = time.perf_counter() - t
            strict, valid, items = parse_output(resp["message"]["content"])
            s = score([i["skill"] for i in items], set(reference[cv_id]), aliases)
            row = {
                "model": model,
                "device": device,
                "mode": mode,
                "cv_id": cv_id,
                "source": source,
                "json_strict": strict,
                "json_valid": valid,
                **s,
                "levels": [i.get("level") for i in items],
                "prompt_tokens": resp.get("prompt_eval_count", 0),
                "output_tokens": resp.get("eval_count", 0),
                "gen_tps": resp.get("eval_count", 0) / max(resp.get("eval_duration", 1) / 1e9, 1e-9),
                "prompt_tps": resp.get("prompt_eval_count", 0) / max(resp.get("prompt_eval_duration", 1) / 1e9, 1e-9),
                "wall_s": round(wall, 2),
                "warmup_s": round(warm_s, 1),
                "mem_bytes": mem_total,
                "vram_bytes": mem_vram,
            }
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(
                f"  {cv_id} json={'✓' if valid else '✗'} tp={s['tp']} fp={s['fp']} fn={s['fn']} "
                f"{row['gen_tps']:.1f} tok/s {wall:.1f} sn"
            )
        unload(model)


# --- Rapor -------------------------------------------------------------------------------------------------------


def report() -> str:
    rows = []
    for path in sorted(RESULTS.glob("*.jsonl")):
        rows += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["device"], r["mode"])].append(r)
    lines = [
        "| Model | Cihaz | Mod | JSON geçerli | Saf JSON | Kesinlik | Duyarlılık | F1 | Taksonomi dışı | "
        "Üretim tok/sn | CV başına sn | Bellek (GB) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for (model, device, mode), rs in sorted(groups.items()):
        tp, fp, fn = (sum(r[k] for r in rs) for k in ("tp", "fp", "fn"))
        p = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * rec / (p + rec) if p + rec else 0.0
        n_pred = sum(r["n_pred"] for r in rs)
        off = sum(r["off_taxonomy"] for r in rs) / n_pred if n_pred else 0.0
        tps = sum(r["gen_tps"] for r in rs) / len(rs)
        wall = sum(r["wall_s"] for r in rs) / len(rs)
        mem = max(r["mem_bytes"] for r in rs) / 2**30
        n = len(rs)
        lines.append(
            f"| {model} | {device} | {mode} | {sum(r['json_valid'] for r in rs)}/{n} | "
            f"{sum(r['json_strict'] for r in rs)}/{n} | {p:.2f} | {rec:.2f} | {f1:.2f} | {off:.0%} | "
            f"{tps:.1f} | {wall:.1f} | {mem:.1f} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    use_utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--models", nargs="+", required=True)
    r.add_argument("--device", choices=["cpu", "gpu"], default="gpu")
    r.add_argument("--mode", choices=["schema", "free"], default="schema")
    r.add_argument("--tag", default="", help="sonuç dosyasının adı (varsayılan: results)")
    sub.add_parser("report")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        run(args.models, args.device, args.mode, args.tag)
    else:
        print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
