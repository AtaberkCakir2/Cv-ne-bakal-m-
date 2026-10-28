"""İlk şema (T-012): 17 tablo, 14 enum, role_skill_stats materialized view.

Kaynak: app/db/models, erd.dbml, docs/veritabani.md. HNSW vektör indeksleri T-013'te ayrı migration ile gelir.

Revision ID: 0001
Revises:
Create Date: 2026-10-25 02:27:21.266648+03:00
"""

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Enum tipleri bir kez oluşturulur; lang_code ve skill_level birden fazla tabloda kullanıldığı için
# tablolarda create_type=False ile sadece referans verilir.
ENUMS: dict[str, tuple[str, ...]] = {
    "user_role": ("user", "admin"),
    "consent_type": ("kvkk_aydinlatma", "acik_riza", "kullanim_kosullari"),
    "token_purpose": ("verify_email", "reset_password"),
    "skill_category": ("dil", "framework", "veritabani", "bulut", "devops", "arac", "metodoloji", "soft"),
    "source_type": ("api", "scrape", "dataset"),
    "lang_code": ("tr", "en"),
    "skill_importance": ("required", "preferred"),
    "scrape_status": ("running", "success", "partial", "failed"),
    "resource_provider": ("youtube", "udemy", "coursera", "btk_akademi", "docs", "blog", "other"),
    "resource_level": ("beginner", "intermediate", "advanced"),
    "skill_level": ("beginner", "intermediate", "advanced", "unknown"),
    "analysis_status": ("queued", "processing", "done", "failed"),
    "analysis_error_code": ("PDF_UNREADABLE", "PDF_TOO_LARGE", "NO_TEXT_FOUND", "LLM_TIMEOUT", "INTERNAL"),
    "skill_kind": ("present", "missing"),
}

# docs/veritabani.md ile aynı tanım. Değişirse yeni migration'da DROP + CREATE yapılır.
ROLE_SKILL_STATS_SQL = """
CREATE MATERIALIZED VIEW role_skill_stats AS
WITH aktif AS (
  SELECT id, role_id FROM job_postings
  WHERE is_active AND role_id IS NOT NULL
    AND (posted_at IS NULL OR posted_at >= current_date - interval '6 months')
), toplam AS (
  SELECT role_id, count(*) AS total_postings FROM aktif GROUP BY role_id
)
SELECT a.role_id, jps.skill_id,
       count(DISTINCT a.id)::int AS posting_count,
       t.total_postings::int AS total_postings,
       round(count(DISTINCT a.id)::numeric / t.total_postings, 4) AS demand_ratio,
       now() AS computed_at
FROM aktif a
JOIN job_posting_skills jps ON jps.posting_id = a.id
JOIN toplam t ON t.role_id = a.role_id
GROUP BY a.role_id, jps.skill_id, t.total_postings
"""


def enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


def timestamps() -> list[sa.Column[datetime]]:
    return [
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    for name, values in ENUMS.items():
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=False)

    # ---------- Katalog ----------
    op.create_table(
        "job_sources",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", enum("source_type"), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("tos_checked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("rate_limit_sec", sa.Numeric(precision=4, scale=1), server_default=sa.text("4"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_sources")),
        sa.UniqueConstraint("name", name=op.f("uq_job_sources_name")),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("synonyms", sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("slug", name=op.f("uq_roles_slug")),
    )
    op.create_index(op.f("ix_roles_synonyms"), "roles", ["synonyms"], postgresql_using="gin")
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("canonical_name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("category", enum("skill_category"), nullable=False),
        sa.Column("synonyms", sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("esco_uri", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(dim=384), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skills")),
        sa.UniqueConstraint("canonical_name", name=op.f("uq_skills_canonical_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_skills_slug")),
    )
    op.create_index(op.f("ix_skills_category"), "skills", ["category"])
    op.create_index(op.f("ix_skills_synonyms"), "skills", ["synonyms"], postgresql_using="gin")
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("provider", enum("resource_provider"), nullable=False),
        sa.Column("language", enum("lang_code"), nullable=False),
        sa.Column("level", enum("resource_level"), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=True),
        sa.Column("is_free", sa.Boolean(), nullable=False),
        sa.Column("is_alive", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills.id"], name=op.f("fk_resources_skill_id_skills"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resources")),
        sa.UniqueConstraint("url", name=op.f("uq_resources_url")),
    )
    op.create_index(op.f("ix_resources_skill_id"), "resources", ["skill_id"])

    # ---------- İlan toplama ----------
    op.create_table(
        "job_postings",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title_raw", sa.Text(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("description_clean", sa.Text(), nullable=False),
        sa.Column("language", enum("lang_code"), nullable=False),
        sa.Column("posted_at", sa.Date(), nullable=True),
        sa.Column("content_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("embedding", Vector(dim=384), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_job_postings_role_id_roles"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["job_sources.id"], name=op.f("fk_job_postings_source_id_job_sources"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_postings")),
        sa.UniqueConstraint("content_hash", name=op.f("uq_job_postings_content_hash")),
        sa.UniqueConstraint("source_id", "external_id", name=op.f("uq_job_postings_source_id_external_id")),
    )
    op.create_index(op.f("ix_job_postings_posted_at"), "job_postings", ["posted_at"])
    op.create_index(op.f("ix_job_postings_role_id"), "job_postings", ["role_id"])
    op.create_table(
        "job_posting_skills",
        sa.Column("posting_id", sa.BigInteger(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("importance", enum("skill_importance"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["posting_id"],
            ["job_postings.id"],
            name=op.f("fk_job_posting_skills_posting_id_job_postings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills.id"], name=op.f("fk_job_posting_skills_skill_id_skills"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("posting_id", "skill_id", name=op.f("pk_job_posting_skills")),
    )
    op.create_index(op.f("ix_job_posting_skills_skill_id"), "job_posting_skills", ["skill_id"])
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", enum("scrape_status"), nullable=False),
        sa.Column("fetched", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("inserted", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("duplicates", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("errors", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("error_log", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["source_id"], ["job_sources.id"], name=op.f("fk_scrape_runs_source_id_job_sources"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scrape_runs")),
    )
    op.create_index(op.f("ix_scrape_runs_source_id"), "scrape_runs", ["source_id", "started_at"])
    op.create_index(op.f("ix_scrape_runs_status"), "scrape_runs", ["status"])

    # ---------- Kullanıcı ve KVKK ----------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("role", enum("user_role"), server_default="user", nullable=False),
        sa.Column("target_role_id", sa.Integer(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["target_role_id"], ["roles.id"], name=op.f("fk_users_target_role_id_roles"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_refresh_tokens_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])
    op.create_table(
        "user_tokens",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", enum("token_purpose"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_tokens_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_user_tokens_token_hash")),
    )
    op.create_index(op.f("ix_user_tokens_user_id"), "user_tokens", ["user_id", "purpose"])
    op.create_table(
        "consents",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("consent_type", enum("consent_type"), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_consents_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_consents")),
        sa.UniqueConstraint(
            "user_id", "consent_type", "version", name=op.f("uq_consents_user_id_consent_type_version")
        ),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("entity", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_audit_logs_user_id_users"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"])

    # ---------- Analizler ----------
    op.create_table(
        "analyses",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("target_role_id", sa.Integer(), nullable=False),
        sa.Column("status", enum("analysis_status"), server_default="queued", nullable=False),
        sa.Column("cv_sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("cv_pages", sa.SmallInteger(), nullable=True),
        sa.Column("match_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("postings_analyzed", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(length=60), nullable=True),
        sa.Column("prompt_version", sa.String(length=60), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", enum("analysis_error_code"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("match_score BETWEEN 0 AND 100", name=op.f("ck_analyses_match_score_range")),
        sa.ForeignKeyConstraint(
            ["target_role_id"], ["roles.id"], name=op.f("fk_analyses_target_role_id_roles"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_analyses_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analyses")),
    )
    op.create_index(op.f("ix_analyses_cv_sha256"), "analyses", ["cv_sha256"])
    op.create_index(op.f("ix_analyses_status"), "analyses", ["status"])
    op.create_index(op.f("ix_analyses_user_id"), "analyses", ["user_id", "created_at"])
    op.create_table(
        "analysis_skills",
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("kind", enum("skill_kind"), nullable=False),
        sa.Column("level", enum("skill_level"), server_default="unknown", nullable=False),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("demand_ratio", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("priority", sa.SmallInteger(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "priority IS NULL OR kind = 'missing'", name=op.f("ck_analysis_skills_priority_only_missing")
        ),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name=op.f("ck_analysis_skills_confidence_range")),
        sa.CheckConstraint("demand_ratio BETWEEN 0 AND 1", name=op.f("ck_analysis_skills_demand_ratio_range")),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["analyses.id"], name=op.f("fk_analysis_skills_analysis_id_analyses"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills.id"], name=op.f("fk_analysis_skills_skill_id_skills"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("analysis_id", "skill_id", name=op.f("pk_analysis_skills")),
    )
    op.create_index(op.f("ix_analysis_skills_skill_id"), "analysis_skills", ["skill_id"])
    op.create_table(
        "analysis_unverified_skills",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("level", enum("skill_level"), server_default="unknown", nullable=False),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        *timestamps(),
        sa.CheckConstraint("confidence BETWEEN 0 AND 1", name=op.f("ck_analysis_unverified_skills_confidence_range")),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name=op.f("fk_analysis_unverified_skills_analysis_id_analyses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_unverified_skills")),
        sa.UniqueConstraint("analysis_id", "name", name=op.f("uq_analysis_unverified_skills_analysis_id_name")),
    )
    op.create_table(
        "analysis_recommendations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("rank", sa.SmallInteger(), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name=op.f("fk_analysis_recommendations_analysis_id_analyses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["resource_id"],
            ["resources.id"],
            name=op.f("fk_analysis_recommendations_resource_id_resources"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills.id"], name=op.f("fk_analysis_recommendations_skill_id_skills"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_analysis_recommendations")),
        sa.UniqueConstraint(
            "analysis_id", "skill_id", "rank", name=op.f("uq_analysis_recommendations_analysis_id_skill_id_rank")
        ),
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name=op.f("ck_feedback_rating_range")),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["analyses.id"], name=op.f("fk_feedback_analysis_id_analyses"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
        sa.UniqueConstraint("analysis_id", name=op.f("uq_feedback_analysis_id")),
    )

    # ---------- İstatistik (3NF: tablo değil view) ----------
    op.execute(ROLE_SKILL_STATS_SQL)
    # CONCURRENTLY yenileme için unique indeks şart.
    op.execute("CREATE UNIQUE INDEX uq_role_skill_stats_role_id_skill_id ON role_skill_stats (role_id, skill_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS role_skill_stats")
    # Bağımlılık sırasının tersi: önce çocuk tablolar.
    for table in (
        "feedback",
        "analysis_recommendations",
        "analysis_unverified_skills",
        "analysis_skills",
        "analyses",
        "audit_logs",
        "consents",
        "user_tokens",
        "refresh_tokens",
        "users",
        "scrape_runs",
        "job_posting_skills",
        "job_postings",
        "resources",
        "skills",
        "roles",
        "job_sources",
    ):
        op.drop_table(table)
    bind = op.get_bind()
    for name in reversed(ENUMS):
        postgresql.ENUM(name=name).drop(bind, checkfirst=False)
    # citext ve vector eklentileri bırakılır: başka şemalar da kullanıyor olabilir, zararsızdır.
