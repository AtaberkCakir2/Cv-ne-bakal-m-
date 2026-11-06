"""OCR karakter doğruluğunu ölçer (T-029 kabul kriteri: 5 taranmış CV'de ≥ %95).

Kullanım:
    python ai/eval/scripts/ocr_accuracy.py [--cv syn-004 syn-009 ...] [--min 0.95]

Her sentetik CV'nin tanım dosyası (`dataset/cv_specs`) bellekte iki kez basılır: dijital hali referans metni verir,
taranmış hali OCR'a girer. Hiçbir dosya yazılmaz. Boşluk farkları sayılmaz; doğruluk = 1 − düzenleme uzaklığı / referans
uzunluğu. Çok sütunlu CV'de iki yolun okuma sırası farklı olabileceği için tek sütunlu CV'ler varsayılandır.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import DEFAULT_DATASET, use_utf8_stdout
from generate_cvs import render_pdf

from ocr import ocr_pdf
from parsing import extract_text

DEFAULT_CVS = ("syn-004", "syn-006", "syn-007", "syn-009", "syn-010")
MIN_ACCURACY = 0.95


def squeeze(text: str) -> str:
    return " ".join(text.split())


def edit_distance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def accuracy(reference: str, read: str) -> float:
    ref, out = squeeze(reference), squeeze(read)
    return max(0.0, 1 - edit_distance(ref, out) / len(ref))


def measure(spec_path: Path) -> float:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    reference = extract_text(render_pdf({**spec, "scanned": False})).text
    return accuracy(reference, ocr_pdf(render_pdf({**spec, "scanned": True})))


def main(argv: list[str] | None = None) -> int:
    use_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--cv", nargs="*", default=DEFAULT_CVS)
    parser.add_argument("--min", type=float, default=MIN_ACCURACY)
    args = parser.parse_args(argv)

    results = {cv_id: measure(args.dataset / "cv_specs" / f"{cv_id}.json") for cv_id in args.cv}
    for cv_id, value in results.items():
        print(f"{cv_id}: %{value * 100:.2f}{'' if value >= args.min else '  ← eşiğin altında'}")
    print(f"\nEn düşük: %{min(results.values()) * 100:.2f} · Eşik: %{args.min * 100:.0f}")
    return 0 if min(results.values()) >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
