# tests/_shared/types.py
from typing import Any, NamedTuple

class TestCase(NamedTuple):
    api_url: str
    params: Any
    expected_code: int

class TestResult(NamedTuple):
    is_success: bool
    status_code: int
    test_status: str
