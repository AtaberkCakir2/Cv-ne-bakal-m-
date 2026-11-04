import uuid

from app.db.enums import AnalysisErrorCode
from app.db.models import Analysis
from app.repositories.analyses import AnalysisRepository
from app.services.analysis_queue import AnalysisQueue, QueueUnavailable
from app.services.cv_validation import validate_cv


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
            self.repository.mark_failed(analysis_id, AnalysisErrorCode.INTERNAL)
            raise
        return analysis_id

    def get(self, analysis_id: uuid.UUID, user_id: uuid.UUID) -> Analysis | None:
        return self.repository.get_owned(analysis_id, user_id)
