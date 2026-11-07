import uuid
from typing import Literal

from pydantic import BaseModel


class AnalysisCreated(BaseModel):
    analysis_id: uuid.UUID
    status: Literal["queued", "processing", "done", "failed"]
