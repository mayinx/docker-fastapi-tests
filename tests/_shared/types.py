# tests/_shared/types.py
from typing import Any, NamedTuple, Optional

class TestCase(NamedTuple):
    api_url: str
    params: Any # suite-specific TestParams (dataclass or NamedTuple instance)
    expected_code: int
    # Only used by CONTENT suite: check sign of returned score
    expected_score: Optional[str] = None  # "positive" | "negative" | None

class TestResult(NamedTuple):
    is_success: bool
    status_code: int
    test_status: str
    score: Optional[float] = None  # e.g. 0.75 | -0.66 | None
