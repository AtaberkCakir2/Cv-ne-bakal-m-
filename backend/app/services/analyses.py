import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError

from app.db.enums import AnalysisErrorCode, AnalysisStatus
from app.db.models import Analysis
from app.repositories.analyses import AnalysisRepository
from app.services.analysis_queue import AnalysisQueue, QueueUnavailable
from app.services.cv_validation import validate_cv

logger = logging.getLogger(__name__)


class UnknownRole(Exception):
    pass


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
        # Bu süreye kadar CV de süre aşımıyla silinmiş olur, tekrar çalıştırılamaz.
        if (
            analysis is not None
            and analysis.status in (AnalysisStatus.QUEUED, AnalysisStatus.PROCESSING)
            and datetime.now(UTC) - analysis.created_at > stale_after
        ):
            self.repository.mark_failed(analysis_id, AnalysisErrorCode.INTERNAL)
        return analysis
