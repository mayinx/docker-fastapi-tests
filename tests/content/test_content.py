"""
API Content Test Suite
----------------------
This script validates that the sentiment API returns *meaningful* results (not just correct auth).

What it checks:
- Calls /v1/sentiment and /v2/sentiment using the alice account.
- For a clearly positive sentence, the returned score must be > 0.
- For a clearly negative sentence, the returned score must be < 0.
  (Note: the score is a float like -0.66 / +0.42 — we only check the sign.)

Reliability:
- Includes an API readiness check (polls GET /status until it returns "1"),
  because docker-compose `depends_on` ensures start order, not actual readiness.

Logging:
- If LOG=1, the test appends its report to LOG_PATH (default: /shared/api_test.log),
  so multiple test containers can write into one shared file.

Exit codes:
- 0 on full success, 1 if any check fails (so CI/CD-style pipelines can fail fast).

Module-run convention (recommended):
    API_ADDRESS=localhost API_PORT=8000 LOG=1 LOG_PATH=./shared/api_test.log \
    python3 -m tests.content.test_content
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

TEST_TYPE = "CONTENT"

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
# - expected_score: expected sentiment sign ("positive" | "negative") for content validation
# ------------------------------------------------------------------------------
test_cases = [
    TestCase(
        api_url="/v1/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="life is beautiful"),
        expected_code=200,
        expected_score="positive",
    ),
    TestCase(
        api_url="/v1/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="that sucks"),
        expected_code=200,
        expected_score="negative",
    ),
    TestCase(
        api_url="/v2/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="life is beautiful"),
        expected_code=200,
        expected_score="positive",
    ),
    TestCase(
        api_url="/v2/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="that sucks"),
        expected_code=200,
        expected_score="negative",
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
