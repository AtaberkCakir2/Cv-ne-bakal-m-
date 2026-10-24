from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class DependencyStatus(BaseModel):
    ok: bool
    latency_ms: float | None = Field(default=None, description="Kontrolün süresi")
    error: str | None = Field(default=None, description="Hata türü (iç ayrıntı içermez)")


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, DependencyStatus] = Field(description="db, redis, ollama")
