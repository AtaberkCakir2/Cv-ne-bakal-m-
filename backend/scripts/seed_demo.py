"""Demo ve ekran testleri için örnek analiz sonucunu test kullanıcısına ekler (T-027 kongre demosu, T-053).

Yapay zekâ işçisi (T-057) sonuç tablolarını doldurana kadar sonuç panosu ancak örnek veriyle gösterilebilir.
Bu betik `contracts/examples/analysis_result.example.json` dosyasını olduğu gibi veri tabanına yazar: ekrandaki
veri sözleşmeyle birebir aynı olur. Gerçek CV kullanılmaz; analiz kaydında sadece sahte bir özet tutulur.

Kullanım (backend/ klasöründe; önce `python scripts/seed_test_user.py`):
    python scripts/seed_demo.py

- Pozisyon, yetkinlik ve kaynaklar yoksa eklenir, varsa olduğu gibi kullanılır (taksonomi yüklü veri tabanında da
  çalışır). Kaynaklar URL'ye göre eşleşir.
- Her çalıştırmada kullanıcıya yeni bir tamamlanmış analiz eklenir; eski demo analizleri silinmez.
- Boş bir veri tabanında eklenen örnek kaynaklar (example.com) katalog uçlarında da görünür; sadece lokal içindir.
- Sadece local/test ortamında çalışır.
"""

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ (app paketi)

from sqlalchemy import or_, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.enums import (  # noqa: E402
    AnalysisStatus,
    LangCode,
    ResourceLevel,
    ResourceProvider,
    SkillCategory,
    SkillKind,
    SkillLevel,
)
from app.db.models import (  # noqa: E402
    Analysis,
    AnalysisRecommendation,
    AnalysisSkill,
    AnalysisUnverifiedSkill,
    Resource,
    Role,
    Skill,
    User,
)
from app.db.session import get_sessionmaker  # noqa: E402

EXAMPLE = Path(__file__).resolve().parents[2] / "contracts" / "examples" / "analysis_result.example.json"
# Gerçek bir CV'nin özeti değil: demo kayıtları veri tabanında bununla ayırt edilir.
DEMO_SHA256 = "d" * 64


def slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def role_for(session: Session, slug: str, name: str) -> Role:
    role = session.scalar(select(Role).where(Role.slug == slug))
    if role is None:
        role = Role(slug=slug, name=name, synonyms=[])
        session.add(role)
        session.flush()
    return role


def skill_for(session: Session, name: str) -> Skill:
    # Taksonomi yetkinlikleri slug'la yükler; ad değişmiş olsa da aynı slug bulunur, unique çakışması olmaz.
    skill = session.scalar(select(Skill).where(or_(Skill.slug == slugify(name), Skill.canonical_name == name)))
    if skill is None:
        # Kategori demo için önemsiz; taksonomi yüklüyse bu dala hiç girilmez.
        skill = Skill(canonical_name=name, slug=slugify(name), category=SkillCategory.ARAC, synonyms=[])
        session.add(skill)
        session.flush()
    return skill


def resource_for(session: Session, skill: Skill, data: dict[str, Any]) -> Resource:
    resource = session.scalar(select(Resource).where(Resource.url == data["url"]))
    if resource is None:
        resource = Resource(
            skill_id=skill.id,
            title=data["title"],
            url=data["url"],
            provider=ResourceProvider(data["provider"]),
            language=LangCode(data["language"]),
            level=ResourceLevel(data["level"]),
            duration_min=data.get("duration_min"),
            is_free=data["is_free"],
        )
        session.add(resource)
        session.flush()
    elif resource.skill_id != skill.id or not resource.is_alive:
        # Havuz Ataberk'in (karar #10): değiştirilmez, sadece haber verilir. Ölü kaynak panoda görünmez.
        print(f"Uyarı: {data['url']} başka bir yetkinliğe bağlı ya da ölü işaretli; panoda eksik çıkabilir.")
    return resource


def main() -> int:
    settings = get_settings()
    if not settings.is_explicit_dev:  # ENVIRONMENT hiç verilmemişse de çalışmaz (canlı veri tabanına yazmasın)
        print(f"Sadece ENVIRONMENT=local/test açıkça verildiğinde çalışır (şu an: {settings.environment}).")
        return 1
    email = os.environ.get("E2E_TEST_EMAIL", "").strip().lower()
    if not email.endswith("@example.com"):
        print("E2E_TEST_EMAIL ayarlanmalı ve @example.com ile bitmeli; önce scripts/seed_test_user.py çalıştırın.")
        return 1
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    with get_sessionmaker()() as session:
        user = session.scalar(select(User).where(User.email == email, User.deleted_at.is_(None)))
        if user is None:
            print(f"{email} bulunamadı; önce scripts/seed_test_user.py çalıştırın.")
            return 1
        role = role_for(session, example["target_role"]["slug"], example["target_role"]["name"])
        now = datetime.now(UTC)
        analysis = Analysis(
            user_id=user.id,
            target_role_id=role.id,
            status=AnalysisStatus.DONE,
            cv_sha256=DEMO_SHA256,
            cv_pages=1,
            match_score=Decimal(str(example["match_score"])),
            postings_analyzed=example["postings_analyzed"],
            model_name=example["model"]["name"],
            prompt_version=example["model"]["prompt_version"],
            duration_ms=72_000,
            completed_at=now,
            created_at=now - timedelta(seconds=72),
        )
        session.add(analysis)
        session.flush()

        for item in example["present_skills"]:
            if item.get("verified") is False:  # taksonomide olmayan yetkinlik: sadece adı tutulur
                session.add(
                    AnalysisUnverifiedSkill(
                        analysis_id=analysis.id,
                        name=item["skill"],
                        level=SkillLevel(item["level"]),
                        confidence=Decimal(str(item["confidence"])),
                    )
                )
                continue
            session.add(
                AnalysisSkill(
                    analysis_id=analysis.id,
                    skill_id=skill_for(session, item["skill"]).id,
                    kind=SkillKind.PRESENT,
                    level=SkillLevel(item["level"]),
                    confidence=Decimal(str(item["confidence"])),
                )
            )
        for item in example["missing_skills"]:
            skill = skill_for(session, item["skill"])
            session.add(
                AnalysisSkill(
                    analysis_id=analysis.id,
                    skill_id=skill.id,
                    kind=SkillKind.MISSING,
                    level=SkillLevel.UNKNOWN,
                    demand_ratio=Decimal(str(item["demand_ratio"])),
                    priority=item["priority"],
                )
            )
            for rank, data in enumerate(item["resources"], start=1):
                session.add(
                    AnalysisRecommendation(
                        analysis_id=analysis.id,
                        skill_id=skill.id,
                        resource_id=resource_for(session, skill, data).id,
                        rank=rank,
                        reason_text=data.get("reason"),
                    )
                )
        session.commit()
        print(f"Demo analizi eklendi: {analysis.id} ({email}, {role.name}).")
        print(f"Web'de: /analiz/{analysis.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
