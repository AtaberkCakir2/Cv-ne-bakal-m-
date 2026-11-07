"""Veritabanındaki ilanları normalize eder: role_id, job_posting_skills ve benzer ilanların pasife alınması.

Aynı taksonomiyle tekrar çalıştırmak aynı sonucu verir; taksonomi değişince (seed-taxonomy) yeniden çalıştırılır.
Pasif ilanlar (ör. EMSCAD) da etiketlenir ama benzer ilan karşılaştırmasına sadece aktif ilanlar girer ve hiçbir
ilan yeniden aktif yapılmaz.
"""

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from app.db.enums import SkillImportance
from app.db.models import JobPosting, JobPostingSkill, JobSource, Role, Skill
from pii import PLACEHOLDERS, mask_posting
from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from collector.clean import Lang
from collector.taxonomy_rows import RoleRow, SkillRow
from etl.dedup import DedupItem, near_duplicates
from etl.roles import RoleMatcher
from etl.skills import SkillTagger

BATCH_SIZE = 500

# İlandaki kişisel veri (işe alımcının adı, telefon, TCKN…) maskeleyicisi. Metni değiştirirse description_clean
# güncellenir. Varsayılan: mask_posting_once.
NameMasker = Callable[[str, Lang], str]

_PLACEHOLDER = re.compile("|".join(re.escape(p) for p in PLACEHOLDERS.values()))
# Yer tutucular maskeleme sırasında harf/rakam içermeyen işaretlerle (Unicode özel kullanım alanı) değiştirilir.
_GUARD = {p: chr(0xE000) + chr(0xE100 + i) + chr(0xE001) for i, p in enumerate(PLACEHOLDERS.values())}
_UNGUARD = {v: k for k, v in _GUARD.items()}
_GUARDED = re.compile("|".join(map(re.escape, _UNGUARD)))


def mask_posting_once(text: str, lang: Lang) -> str:
    """Burak'ın T-030 maskeleyicisi `pii.mask_posting` (kurallar; NER yok, sonuç tekrarlanabilir); normalize her gece
    tüm ilanlarda tekrar çalıştığı için önceki çalışmanın koyduğu etiketlere dokunmaz.

    mask_posting kendi etiketini yeniden maskeleyebiliyor: "name: X" → "[AD SOYAD]", sonra ad yayma kuralı "SOYAD"
    kelimesini her yerde maskeleyip "[AD [AD SOYAD]]" üretiyor ve her gece bir kat daha ekleniyordu.
    """
    guarded = _PLACEHOLDER.sub(lambda m: _GUARD[m.group()], text)
    return _GUARDED.sub(lambda m: _UNGUARD[m.group()], mask_posting(guarded, lang))


@dataclass
class NormalizeResult:
    postings: int = 0
    with_role: int = 0
    with_skills: int = 0
    skill_links: int = 0
    masked: int = 0
    deactivated: int = 0


def _ids(session: Session, model: type[Role] | type[Skill]) -> dict[str, int]:
    return dict(session.execute(select(model.slug, model.id).where(model.is_active)).tuples().all())


def normalize(
    session: Session,
    skills: list[SkillRow],
    roles: list[RoleRow],
    *,
    mask_names: NameMasker | None = mask_posting_once,
) -> NormalizeResult:
    role_ids, skill_ids = _ids(session, Role), _ids(session, Skill)
    missing = {s.slug for s in skills} - skill_ids.keys() | {r.slug for r in roles} - role_ids.keys()
    if missing:
        raise ValueError(f"taksonomi veritabanında yok, önce seed-taxonomy çalıştırın: {sorted(missing)[:10]}")
    matcher, tagger = RoleMatcher(roles, skills), SkillTagger(skills)
    result = NormalizeResult()
    dedup_items: list[DedupItem] = []

    rows = session.execute(
        select(
            JobPosting.id,
            JobPosting.title_raw,
            JobPosting.description_clean,
            JobPosting.language,
            JobPosting.company,
            JobPosting.posted_at,
            JobPosting.is_active,
        ).order_by(JobPosting.id)
    ).all()
    for batch in (rows[i : i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)):
        updates: list[dict[str, Any]] = []
        links: list[dict[str, Any]] = []
        for pid, title, text, lang, company, posted_at, active in batch:
            values: dict[str, Any] = {"id": pid}
            if mask_names and (masked := mask_names(text, lang.value)) != text:
                text = values["description_clean"] = masked
                result.masked += 1
            slug = matcher.match(title, lang.value)
            values["role_id"] = role_ids[slug] if slug else None
            updates.append(values)
            tags = tagger.tag(f"{title}\n\n{text}", lang.value)
            links += [
                {"posting_id": pid, "skill_id": skill_ids[t.slug], "importance": SkillImportance(t.importance)}
                for t in tags
            ]
            result.postings += 1
            result.with_role += slug is not None
            result.with_skills += bool(tags)
            result.skill_links += len(tags)
            if active:
                dedup_items.append(DedupItem(pid, company, slug, posted_at, text))

        ids = [u["id"] for u in updates]
        session.execute(update(JobPosting), updates)
        session.execute(delete(JobPostingSkill).where(JobPostingSkill.posting_id.in_(ids)))
        if links:
            session.execute(insert(JobPostingSkill), links)
        session.commit()

    if drop := near_duplicates(dedup_items):
        session.execute(update(JobPosting).where(JobPosting.id.in_(drop)).values(is_active=False))
        session.commit()
    result.deactivated = len(drop)
    return result


def to_contract(
    posting: JobPosting, source: str, role_slug: str, skills: list[tuple[str, SkillImportance]]
) -> dict[str, Any]:
    """contracts/job_posting.schema.json biçimi (Ataberk → Burak). Önce required, sonra preferred yetkinlikler."""
    return {
        "id": posting.id,
        "source": source,
        "external_id": posting.external_id,
        "url": posting.url,
        "title_raw": posting.title_raw,
        "role_slug": role_slug,
        "company": posting.company,
        "location": posting.location,
        "description_clean": posting.description_clean,
        "language": posting.language.value,
        "posted_at": posting.posted_at.isoformat() if posting.posted_at else None,
        "skills": [
            {"skill": name, "importance": imp.value}
            for name, imp in sorted(skills, key=lambda s: s[1] != SkillImportance.REQUIRED)
        ],
    }


def iter_contract(session: Session, *, limit: int | None = None) -> Iterator[dict[str, Any]]:
    """Aktif ve pozisyonu belli ilanlar (role_slug sözleşmede zorunlu)."""
    query = (
        select(JobPosting, JobSource.name, Role.slug)
        .join(JobSource, JobSource.id == JobPosting.source_id)
        .join(Role, Role.id == JobPosting.role_id)
        .where(JobPosting.is_active)
        .order_by(JobPosting.id)
        .limit(limit)
    )
    postings = session.execute(query).tuples().all()
    skills: dict[int, list[tuple[str, SkillImportance]]] = {}
    for pid, name, imp in session.execute(
        select(JobPostingSkill.posting_id, Skill.canonical_name, JobPostingSkill.importance)
        .join(Skill, Skill.id == JobPostingSkill.skill_id)
        .where(JobPostingSkill.posting_id.in_([p.id for p, _, _ in postings]))
        .order_by(JobPostingSkill.posting_id, Skill.canonical_name)
    ).tuples():
        skills.setdefault(pid, []).append((name, imp))
    for posting, source, role_slug in postings:
        yield to_contract(posting, source, role_slug, skills.get(posting.id, []))
