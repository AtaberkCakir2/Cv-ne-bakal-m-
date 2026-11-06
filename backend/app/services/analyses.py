import uuid

from app.repositories.analyses import AnalysisRecord, AnalysisRepository
from app.services.analysis_queue import AnalysisQueue
from app.services.cv_validation import validate_cv


class AnalysisService:
    def __init__(self, repository: AnalysisRepository, queue: AnalysisQueue) -> None:
        self.repository = repository
        self.queue = queue

    def create(self, content: bytes, content_type: str | None, target_role_id: int) -> AnalysisRecord:
        """CV'yi doğrular, kaydı oluşturur ve kuyruğa verir. Doğrulama hatasında CvRejected fırlatır."""
        cv = validate_cv(content, content_type)
        record = AnalysisRecord(id=uuid.uuid4(), target_role_id=target_role_id, cv_sha256=cv.sha256, cv_pages=cv.pages)
        self.repository.add(record)
        self.queue.enqueue(record, cv.content)
        return record

    def get(self, analysis_id: uuid.UUID) -> AnalysisRecord | None:
        return self.repository.get(analysis_id)
