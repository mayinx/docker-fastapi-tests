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

import requests
from typing import NamedTuple
import textwrap

from dataclasses import dataclass

from tests._shared.types import TestCase, TestResult

from tests._shared.params import iter_params, params_dict

from tests._shared.config import load_config
from tests._shared.readiness import wait_for_api
from tests._shared.logging import (
    ensure_log_dir,
    log_suite_start,
    log_suite_finished,
    log_api_not_ready,
    log_to_file,
)

# --- Configuration (via Environment Variables) ---
cfg = load_config()
ensure_log_dir(cfg)

TEST_TYPE = "AUTHORIZATION"

# --- Suite-Specific TestParams ---
# - The only thing each test module must define: Each suite defines its own TestParams shape 
#   (fields can differ per suite).
# - Shared helpers (iter_params / params_dict) stay generic and keep logging + requests DRY.
@dataclass(frozen=True)
class TestParams:
    username: str
    password: str
    sentence: str

# --- Test Data ---
# Define Test Data using TestCase, whose structure is shared across suites:
# - api_url: endpoint path (e.g. "/v1/sentiment")
# - params: suite-specific TestParams instance
# - expected_code: HTTP status we expect for this case
test_cases = [
    TestCase(
        api_url="/v1/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="Hui! What a wonderful wonderful world!"),
        expected_code=200,
    ),
    TestCase(
        api_url="/v2/sentiment",
        params=TestParams(username="alice", password="wonderland", sentence="Shitty day!"),
        expected_code=200,
    ),
    TestCase(
        api_url="/v1/sentiment",
        params=TestParams(
            username="bob",
            password="builder",
            sentence="Building - Construction Sites - Building again  - Construction sites ... - every shitday the same bullshit!",
        ),
        expected_code=200,
    ),
    TestCase(
        api_url="/v2/sentiment",
        params=TestParams(username="bob", password="builder", sentence="Day off! Yes! Aweswome!"),
        expected_code=403,
    ),
]

# params_dict() converts any TestParams dataclass to a dict for requests.get(params=...)
# (So the request code never cares which fields exist.)
def check_test_case(test_case: TestCase) -> TestResult:
    """
    Executes a GET request for a specific user and validates the HTTP status code.
    
    Returns:
        TestResult: An object containing success status and response details.
    """    
    try: 
        result = requests.get(
            url=f"http://{cfg.api_address}:{cfg.api_port}{test_case.api_url}",
            params=params_dict(test_case.params),
            timeout=cfg.timeout,
        )  
        
        # Compare actual HTTP code vs the one defined in the TestCase
        is_success = result.status_code == test_case.expected_code

        return TestResult(
            is_success=is_success, 
            status_code=result.status_code, 
            test_status="SUCCESS" if is_success else "FAILURE"    
        )
    except requests.exceptions.RequestException as e:
        # Handle timeouts, DNS issues, or connection refused without crashing
        return TestResult(
            is_success=False,
            status_code=0, # 0 => no HTTP response received
            test_status=f"ERROR: {type(e).__name__}"
        )          

# iter_params() yields (key, value) pairs from TestParams
# so logging works for any suite without hardcoding param names.
def log_result(test_no: int, test_case: TestCase, test_result: TestResult):
    """Formats and writes a single test result to stdout and optionally a file."""    
    
    # Format request params dynamically (works for any TestParams shape)
    params_lines = "\n".join(f'| {k}="{v}"' for k, v in iter_params(test_case.params))
    
    output = f"""==========================================
    {TEST_TYPE} TEST NO. {test_no}
==========================================
request done at "{test_case.api_url}"
{params_lines}
expected result = {test_case.expected_code}
actual result = {test_result.status_code}
==> TEST STATUS: {test_result.test_status}""".strip()

    # write log to console
    print(output, end="\n\n")
    log_to_file(cfg, output)     

def main() -> int:
    """
    Main entry point for the test script. Coordinates initialization, execution, and exit codes.
    """    
    log_suite_start(cfg, TEST_TYPE, len(test_cases))

    # Ensure API readiness before running tests
    if not wait_for_api(cfg):
        log_api_not_ready(cfg, TEST_TYPE)
        return 1

    all_assertions_met = True

    for test_no, test_case in enumerate(test_cases, start=1):
        test_result = check_test_case(test_case)
        log_result(test_no, test_case, test_result)

        if not test_result.is_success:
            all_assertions_met = False

    log_suite_finished(cfg, TEST_TYPE, all_assertions_met)
    return 0 if all_assertions_met else 1
        
if __name__ == "__main__":
    # Raise SystemExit to ensure the return value of main() is used as the shell exit code
    raise SystemExit(main())   

        