"""
API Authorization Test Suite
----------------------------
This script validates the API authorization behavior by calling sentiment endpoints
with known credentials + sentences and checking expected HTTP status codes.

It includes a readiness check (polling GET /status) to ensure the API is up before testing
(because docker-compose `depends_on` ensures start order, not readiness).

If LOG="1", the script appends the report to LOG_PATH (default: /shared/api_test.log),
so multiple test containers can share one log file later.

Exits with 0 on success, 1 on failure (so CI/CD-style pipelines can fail fast).

By default it targets the API via Docker Compose internal DNS `api:8000`
(API_ADDRESS defaults to "api", API_PORT defaults to 8000). For host-run dev, set
API_ADDRESS=localhost.

Module-run convention (recommended):
    API_ADDRESS=localhost API_PORT=8000 LOG=1 LOG_PATH=./shared/api_test.log \
    python3 -m tests.authorization.test_authorization
"""

from dataclasses import dataclass

from tests._shared.types import TestCase
from tests._shared.config import load_config
from tests._shared.readiness import wait_for_api
from tests._shared.logging import (
    ensure_log_dir,
    log_suite_start,
    log_suite_finished,
    log_api_not_ready,
    log_result,
)
from tests._shared.runner import run_test_case

# ------------------------------------------------------------------------------
# Config (shared across all suites)
# ------------------------------------------------------------------------------
cfg = load_config()
ensure_log_dir(cfg)

TEST_TYPE = "AUTHORIZATION"

# ------------------------------------------------------------------------------
# Suite-specific request params
# - Each suite defines its own TestParams shape.
# - Shared helpers stay generic and work with any dataclass params.
# ------------------------------------------------------------------------------
@dataclass(frozen=True)
class TestParams:
    username: str
    password: str
    sentence: str

# ------------------------------------------------------------------------------
# Test cases
# - api_url: endpoint path
# - params: suite-specific TestParams
# - expected_code: expected HTTP status
# ------------------------------------------------------------------------------
test_cases = [
    TestCase(
        api_url="/v1/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="I just fixed it… by rebooting. I am a genius."),
        expected_code=200,
    ),
    TestCase(
        api_url="/v2/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="My code works on my machine — and my machine is very supportive."),
        expected_code=200,
    ),
    TestCase(
        api_url="/v1/sentiment",
        params=TestParams(
            username="bob",
            password="builder",
            sentence="Coffee status: compiled. Human status: still linking...",
        ),
        expected_code=200,
    ),
    TestCase(
        api_url="/v2/sentiment",
        params=TestParams(username="bob", password="builder", sentence="I named the bug ‘Gerald’. Gerald is back."),
        expected_code=403,
    ),
]

def main() -> int:
    """Run the CONTENT suite end-to-end and return a process exit code (0/1)."""
    log_suite_start(cfg, TEST_TYPE, len(test_cases))

    # Readiness gate: fail fast with a clear log if the API never becomes healthy.
    if not wait_for_api(cfg):
        log_api_not_ready(cfg, TEST_TYPE)
        return 1

    all_assertions_met = True

    for test_no, test_case in enumerate(test_cases, start=1):
        test_result = run_test_case(cfg, test_case)
        log_result(cfg, TEST_TYPE, test_no, test_case, test_result)

        if not test_result.is_success:
            all_assertions_met = False

    log_suite_finished(cfg, TEST_TYPE, all_assertions_met)
    return 0 if all_assertions_met else 1

# Only run the test suite when this file is executed directly (or via `python -m ...`).
# If the module is imported (e.g., by shared tooling), do NOT auto-run the tests.
if __name__ == "__main__":
    # Exit the process with main()'s return code (0=success, 1=failure),
    # so Docker/CI pipelines can fail fast when a test fails.
    raise SystemExit(main())