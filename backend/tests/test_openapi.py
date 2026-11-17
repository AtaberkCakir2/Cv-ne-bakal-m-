"""OpenAPI tanımı (T-080): hata şeması, örnekler ve repodaki dışa aktarılmış kopyaların güncelliği."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

from app.schemas.analyses import ANALYSIS_EXAMPLE, AnalysisOut

REPO = Path(__file__).resolve().parents[2]
CONTRACT_EXAMPLE = REPO / "contracts" / "examples" / "analysis_result.example.json"


def _export_module() -> Any:
    spec = importlib.util.spec_from_file_location("export_openapi", REPO / "backend" / "scripts" / "export_openapi.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _operations(schema: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    return [(path, method, op) for path, ops in schema["paths"].items() for method, op in ops.items()]


@pytest.fixture
def schema(app: FastAPI) -> dict[str, Any]:
    return app.openapi()


def test_errors_are_documented_as_problem(schema: dict[str, Any]) -> None:
    components = schema["components"]["schemas"]
    assert "Problem" in components
    assert "HTTPValidationError" not in components  # API bu biçimi hiç dönmez
    for path, method, op in _operations(schema):
        for status, response in op["responses"].items():
            if status[0] in "45" and path != "/api/v1/health/ready":
                content = response["content"]
                assert content == {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}}, (
                    f"{method.upper()} {path} {status}"
                )


def test_readiness_503_keeps_its_own_body(schema: dict[str, Any]) -> None:
    response = schema["paths"]["/api/v1/health/ready"]["get"]["responses"]["503"]
    assert response["content"]["application/json"]["schema"]["$ref"].endswith("/ReadinessResponse")


def test_every_operation_has_summary_description_and_rate_limit(schema: dict[str, Any]) -> None:
    for path, method, op in _operations(schema):
        assert op.get("summary") and op.get("description"), f"{method.upper()} {path}"
        if not path.endswith("/health"):
            assert "429" in op["responses"], f"{method.upper()} {path}"


def test_authenticated_operations_document_401(schema: dict[str, Any]) -> None:
    for path, method, op in _operations(schema):
        if path.startswith(("/api/v1/users", "/api/v1/analyses")):
            assert "401" in op["responses"], f"{method.upper()} {path}"


def test_request_bodies_have_examples(schema: dict[str, Any]) -> None:
    components = schema["components"]["schemas"]
    for path, method, op in _operations(schema):
        body = op.get("requestBody", {}).get("content", {}).get("application/json")
        if body:
            name = body["schema"]["$ref"].rsplit("/", 1)[1]
            assert components[name].get("examples"), f"{method.upper()} {path}: {name}"


def test_analysis_example_matches_contract() -> None:
    contract = json.loads(CONTRACT_EXAMPLE.read_text(encoding="utf-8"))
    assert contract == ANALYSIS_EXAMPLE
    AnalysisOut.model_validate(ANALYSIS_EXAMPLE)


def test_exported_copies_are_current() -> None:
    export = _export_module()
    text = export.render(export.build_schema())
    stale = [str(t.relative_to(REPO)) for t in export.TARGETS if not export.is_current(t, text)]
    assert not stale, (
        f"Güncel değil: {stale}. Çalıştırın: python scripts/export_openapi.py && (cd web && npm run gen:api)"
    )
