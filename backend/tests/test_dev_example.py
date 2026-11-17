import json

import pytest

from app.core.config import REPO_ROOT
from app.services.analyzer import EXAMPLE_RESULT

CONTRACT_EXAMPLE = REPO_ROOT / "contracts" / "examples" / "analysis_result.example.json"


@pytest.mark.skipif(not CONTRACT_EXAMPLE.exists(), reason="repo dışında (ör. Docker imajında) contracts/ yok")
def test_dev_example_matches_contract_example() -> None:
    # Sözleşmedeki örnek değişirse backend'deki kopya da güncellenmeli: cp contracts/examples/... backend/app/dev/
    assert json.loads(EXAMPLE_RESULT.read_text(encoding="utf-8")) == json.loads(
        CONTRACT_EXAMPLE.read_text(encoding="utf-8")
    )
