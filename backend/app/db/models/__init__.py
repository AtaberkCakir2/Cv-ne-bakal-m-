"""Tüm modeller. Alembic Base.metadata'yı buradan okur; yeni model dosyası eklenince buraya da eklenir."""

from app.db.models.analysis import Analysis, AnalysisRecommendation, AnalysisSkill, AnalysisUnverifiedSkill, Feedback
from app.db.models.audit import AuditLog
from app.db.models.catalog import Resource, Role, Skill
from app.db.models.jobs import JobPosting, JobPostingSkill, JobSource, ScrapeRun
from app.db.models.user import Consent, RefreshToken, User, UserToken

__all__ = [
    "Analysis",
    "AnalysisRecommendation",
    "AnalysisSkill",
    "AnalysisUnverifiedSkill",
    "AuditLog",
    "Consent",
    "Feedback",
    "JobPosting",
    "JobPostingSkill",
    "JobSource",
    "RefreshToken",
    "Resource",
    "Role",
    "ScrapeRun",
    "Skill",
    "User",
    "UserToken",
]
