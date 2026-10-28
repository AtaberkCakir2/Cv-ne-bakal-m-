"""Veri seti scriptlerinin ortak yardımcıları. Sadece standart kütüphane kullanır."""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EVAL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = EVAL_DIR / "dataset"
DEFAULT_SKILLS = DEFAULT_DATASET / "skills_provisional.json"

TEAM = ("ataberk", "burak", "anil")
LEVELS = ("beginner", "intermediate", "advanced", "unknown")
SOURCES = ("real", "synthetic")
LANGUAGES = ("tr", "en")
LAYOUTS = ("single_column", "multi_column", "table", "creative")
CV_ID_RE = re.compile(r"^(cv|syn)-(\d{3,})$")
PENDING_KEY = "_karar_bekleyen"

# cv numarası mod 3 → (etiketleyiciler, hakem). README'deki tabloyla aynı.
ASSIGNMENT = {
    0: (("burak", "ataberk"), "anil"),
    1: (("burak", "anil"), "ataberk"),
    2: (("ataberk", "anil"), "burak"),
}


def use_utf8_stdout() -> None:
    """Windows konsolunda Türkçe karakter ve ✓/✗ basılabilsin diye."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


@dataclass
class Skills:
    names: set[str]
    by_alias: dict[str, str]  # küçük harfli ad/eş anlamlı → standart ad

    def __contains__(self, name: object) -> bool:
        return name in self.names

    def suggest(self, name: str) -> str | None:
        return self.by_alias.get(name.strip().lower())


def load_skill_names(path: Path) -> Skills:
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {s["canonical_name"] for s in data["skills"]}
    by_alias: dict[str, str] = {}
    for s in data["skills"]:
        for alias in [s["canonical_name"], *s.get("synonyms", [])]:
            by_alias.setdefault(alias.lower(), s["canonical_name"])
    return Skills(names, by_alias)


def load_manifest(dataset: Path, report: Report) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    path = dataset / "manifest.csv"
    if not path.exists():
        report.error(f"{path} bulunamadı")
        return rows
    with path.open(encoding="utf-8", newline="") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            where = f"manifest.csv:{line_no}"
            cv_id = (row.get("cv_id") or "").strip()
            if not CV_ID_RE.match(cv_id):
                report.error(f"{where}: geçersiz cv_id '{cv_id}' (ör. cv-001, syn-001)")
                continue
            if cv_id in rows:
                report.error(f"{where}: {cv_id} iki kez yazılmış")
                continue
            _check_enum(report, where, "source", row.get("source"), SOURCES)
            _check_enum(report, where, "language", row.get("language"), LANGUAGES)
            _check_enum(report, where, "layout", row.get("layout"), LAYOUTS)
            _check_enum(report, where, "scanned", row.get("scanned"), ("true", "false"))
            if not (row.get("pages") or "").strip().isdigit():
                report.error(f"{where}: pages sayı olmalı")
            expected_prefix = "syn" if row.get("source") == "synthetic" else "cv"
            if not cv_id.startswith(expected_prefix + "-"):
                report.error(f"{where}: source={row.get('source')} için cv_id '{expected_prefix}-' ile başlamalı")
            if row.get("source") == "real" and not (row.get("consent_id") or "").strip():
                report.error(f"{where}: gerçek CV için consent_id (izin formu no) zorunlu")
            rows[cv_id] = row
    return rows


def _check_enum(report: Report, where: str, name: str, value: str | None, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        report.error(f"{where}: {name}='{value}' geçersiz; izinli: {', '.join(allowed)}")


def cv_number(cv_id: str) -> int:
    m = CV_ID_RE.match(cv_id)
    return int(m.group(2)) if m else 0


def assignment(cv_id: str) -> tuple[tuple[str, str], str]:
    return ASSIGNMENT[cv_number(cv_id) % 3]


def read_json(path: Path, report: Report) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        report.error(f"{path}: okunamadı ({e})")
        return None
    if not isinstance(data, dict):
        report.error(f"{path}: JSON nesnesi olmalı")
        return None
    return data


def validate_skills(path: Path, items: Any, skill_names: Skills, report: Report) -> list[dict[str, Any]]:
    """Yetkinlik listesini doğrular; geçerli öğeleri döner."""
    if not isinstance(items, list):
        report.error(f"{path}: 'skills' liste olmalı")
        return []
    valid: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, item in enumerate(items):
        where = f"{path}: skills[{i}]"
        if not isinstance(item, dict) or not isinstance(item.get("skill"), str):
            report.error(f"{where}: {{skill, level, years}} nesnesi olmalı")
            continue
        name = item["skill"]
        if name != name.strip():
            report.error(f"{where}: '{name}' başında/sonunda boşluk var")
        elif name.startswith("?"):
            suggestion = skill_names.suggest(name[1:])
            if suggestion:
                report.error(f"{where}: '{name}' listede var → '{suggestion}' yazın")
        elif name not in skill_names:
            suggestion = skill_names.suggest(name)
            if suggestion:
                report.error(f"{where}: '{name}' standart ad değil → '{suggestion}' yazın")
            else:
                report.error(f"{where}: '{name}' listede yok (yeni ise başına ? koyun)")
        if name in seen:
            report.error(f"{where}: '{name}' iki kez yazılmış")
        seen.add(name)
        if item.get("level") not in LEVELS:
            report.error(f"{where}: level '{item.get('level')}' geçersiz; izinli: {', '.join(LEVELS)}")
        years = item.get("years")
        if years is not None and (not isinstance(years, int) or isinstance(years, bool) or years < 0):
            report.error(f"{where}: years null veya 0+ tam sayı olmalı")
        valid.append(item)
    return valid


def load_labels(dataset: Path, skill_names: Skills, report: Report) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """{cv_id: {etiketleyici: skills}} döner."""
    labels: dict[str, dict[str, list[dict[str, Any]]]] = {}
    root = dataset / "labels"
    if not root.exists():
        return labels
    for cv_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(cv_dir.glob("*.json")):
            data = read_json(path, report)
            if data is None:
                continue
            if data.get("cv_id") != cv_dir.name:
                report.error(f"{path}: cv_id '{data.get('cv_id')}' klasör adıyla ({cv_dir.name}) aynı değil")
            if data.get("annotator") != path.stem:
                report.error(f"{path}: annotator '{data.get('annotator')}' dosya adıyla ({path.stem}) aynı değil")
            if path.stem not in TEAM:
                report.error(f"{path}: etiketleyici '{path.stem}' ekipte yok ({', '.join(TEAM)})")
            labels.setdefault(cv_dir.name, {})[path.stem] = validate_skills(
                path, data.get("skills"), skill_names, report
            )
    return labels


def load_gold(dataset: Path, skill_names: Skills, report: Report) -> dict[str, list[dict[str, Any]]]:
    gold: dict[str, list[dict[str, Any]]] = {}
    root = dataset / "gold"
    if not root.exists():
        return gold
    for path in sorted(root.glob("*.json")):
        data = read_json(path, report)
        if data is None:
            continue
        if data.get("cv_id") != path.stem:
            report.error(f"{path}: cv_id '{data.get('cv_id')}' dosya adıyla aynı değil")
        if data.get(PENDING_KEY):
            report.error(f"{path}: '{PENDING_KEY}' listesinde çözülmemiş {len(data[PENDING_KEY])} yetkinlik var")
        if data.get("adjudicator") not in TEAM:
            report.error(f"{path}: adjudicator '{data.get('adjudicator')}' ekipte yok")
        gold[path.stem] = validate_skills(path, data.get("skills"), skill_names, report)
    return gold
