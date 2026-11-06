import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError

from app.db.enums import AnalysisErrorCode, AnalysisStatus
from app.db.models import Analysis, Resource
from app.repositories.analyses import AnalysisRepository
from app.services.analysis_queue import AnalysisQueue, QueueUnavailable
from app.services.cv_validation import validate_cv

logger = logging.getLogger(__name__)


class UnknownRole(Exception):
    pass


class AnalysisNotFinished(Exception):
    """Geri bildirim sadece tamamlanmış analize verilir."""


@dataclass(frozen=True)
class ResultCatalog:
    skill_names: dict[int, str]
    resources: dict[int, Resource]


class AnalysisService:
    def __init__(self, repository: AnalysisRepository, queue: AnalysisQueue) -> None:
        self.repository = repository
        self.queue = queue

    def create(self, user_id: uuid.UUID, content: bytes, content_type: str | None, target_role_id: int) -> uuid.UUID:
        """CV'yi doğrular, kaydı oluşturur ve kuyruğa verir. CvRejected, UnknownRole veya QueueUnavailable fırlatır."""
        cv = validate_cv(content, content_type)
        if not self.repository.role_exists(target_role_id):
            raise UnknownRole
        analysis_id = self.repository.add(user_id, target_role_id, cv.sha256, cv.pages)
        try:
            self.queue.enqueue(analysis_id, cv.content)
        except QueueUnavailable:
            try:
                self.repository.mark_failed(analysis_id, AnalysisErrorCode.INTERNAL)
            except SQLAlchemyError as exc:  # kullanıcı yine 503 alsın; satırı askı kontrolü kapatır
                logger.warning("analysis_mark_failed_error: %s", type(exc).__name__)
            raise
        return analysis_id

    def get(self, analysis_id: uuid.UUID, user_id: uuid.UUID, stale_after: timedelta) -> Analysis | None:
        analysis = self.repository.get_owned(analysis_id, user_id)
        # İşçi öldüyse veya sert süre sınırına takıldıysa satırı düzeltecek kimse yok: kullanıcı sonsuza dek beklemesin.
        # Bu süreye kadar CV de süre aşımıyla silinmiş olur, tekrar çalıştırılamaz. Koşullu UPDATE: işçi arada
        # sonucu yazdıysa ezilmez.
        cutoff = datetime.now(UTC) - stale_after
        if (
            analysis is not None
            and analysis.status in (AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING)
            and analysis.created_at < cutoff
        ):
            self.repository.fail_stale(user_id, cutoff)
        return analysis

    def history(
        self, user_id: uuid.UUID, limit: int, offset: int, stale_after: timedelta
    ) -> tuple[list[Analysis], int]:
        """Kullanıcının analizleri, yeniden eskiye. Askıdakiler önce başarısız sayılır (get ile aynı kural)."""
        self.repository.fail_stale(user_id, datetime.now(UTC) - stale_after)
        return self.repository.list_owned(user_id, limit, offset)

    def delete(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Başkasının analizi veya zaten silinmiş analiz için False (404)."""
        return self.repository.soft_delete(analysis_id, user_id)

    def give_feedback(self, analysis_id: uuid.UUID, user_id: uuid.UUID, rating: int, comment: str | None) -> bool:
        """Başkasının veya silinmiş analiz için False (404); bitmemiş analizde AnalysisNotFinished (409)."""
        analysis = self.repository.get_owned(analysis_id, user_id)
        if analysis is None:
            return False
        if analysis.status != AnalysisStatus.DONE:
            raise AnalysisNotFinished
        self.repository.save_feedback(analysis_id, rating, comment)
        return True

    def catalog_for(self, analysis: Analysis) -> ResultCatalog:
        """Sonuçtaki yetkinlik adları ve önerilen kaynaklar (analiz tabloları sadece kimlik tutar)."""
        skill_ids = {s.skill_id for s in analysis.skills} | {r.skill_id for r in analysis.recommendations}
        return ResultCatalog(
            self.repository.skill_names(skill_ids),
            self.repository.resources({r.resource_id for r in analysis.recommendations}),
        )
