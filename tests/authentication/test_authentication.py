"""
API Authentication Test Suite
-----------------------------
This script validates the API authentication behavior by calling GET /permissions
with 3 sets of known credentials and checking the expected HTTP status codes.

It includes a readiness check (polling GET /status) to ensure the API is up before testing
(because docker-compose `depends_on` ensures start order, not readiness).

If LOG="1", the script appends the report to LOG_PATH (default: /shared/api_test.log),
so multiple test containers can share one log file later.

Exits with 0 on success, 1 on failure (so CI/CD-style pipelines can fail fast).

By default it targets the API via Docker Compose internal DNS `api:8000`
(API_ADDRESS defaults to "api", API_PORT defaults to 8000). For host-run dev, set
API_ADDRESS=localhost.

Usage:
    API_ADDRESS=localhost API_PORT=8000 LOG=1 LOG_PATH=./shared/api_test.log \
    python3 tests/authentication/test_authentication.py
"""

import datetime
import os
import time
import requests
from typing import NamedTuple
import textwrap

# --- Configuration (via Environment Variables) ---
API_ADDRESS = os.environ.get("API_ADDRESS", "api")
API_PORT = int(os.environ.get("API_PORT", "8000"))
LOG = os.environ.get('LOG', "0") 

LOG_PATH = os.environ.get("LOG_PATH", "/shared/api_test.log")
TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "5"))

# Ensure log directory exists if logging is enabled   
log_dir = os.path.dirname(LOG_PATH)
if LOG == "1" and log_dir:
    os.makedirs(log_dir, exist_ok=True)    

# --- Data Structures ---
class TestCase(NamedTuple):
    username: str
    password: str
    expected_code: int

class TestResult(NamedTuple):
    is_success: bool
    status_code: int
    test_status: str

# --- Test Data ---
test_cases = [
    TestCase("alice", "wonderland", 200),
    TestCase("bob", "builder", 200),
    TestCase("clementine", "mandarine", 403),
]

def wait_for_api(timeout_s: int = 40) -> bool:
    """
    Polls the API /status endpoint until it returns "1" or timeout is reached.
    Essential for Docker environments where services start at different speeds.
    """    
    url = f"http://{API_ADDRESS}:{API_PORT}/status"
    start = time.time()
    
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=TIMEOUT)
             # API is considered 'Ready' only if status is 200 and body is "1"
            if r.status_code == 200 and r.text.strip() == "1":
                return True
        except requests.exceptions.RequestException:
             # Silently ignore connection errors during the waiting phase
            pass
        time.sleep(1)
    return False

def check_test_case(test_case: TestCase) -> TestResult:
    """
    Executes a GET request for a specific user and validates the HTTP status code.
    
    Returns:
        TestResult: An object containing success status and response details.
    """    
    try: 
        result = requests.get(
             url=f"http://{API_ADDRESS}:{API_PORT}/permissions",
            params= {
                'username': test_case.username,
                'password': test_case.password 
            },
            timeout=TIMEOUT,
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

def log_result(test_no: int, test_case: TestCase, test_result: TestResult):
    """Formats and writes a single test result to stdout and optionally a file."""    
    output = textwrap.dedent(f'''
    ==========================================
        Authentication test No. {test_no}
    ==========================================
    request done at "/permissions"
    | username="{test_case.username}"
    | password="{test_case.password}"
    expected result = {test_case.expected_code}
    actual result = {test_result.status_code}
    ==> TEST STATUS: {test_result.test_status}
    ''').strip()

    # write log to console
    print(output, end="\n\n")
    log_to_file(output)     

def log_api_not_ready():
    """Logs a critical failure if the API readiness check fails."""
    output = textwrap.dedent("""
    ==========================================
        TEST-SUITE 'AUTHENTICATION' ABORTED
    ==========================================
    API readiness check FAILED
    expected /status => "1"
    ==> TEST STATUS: FAILURE
    """).strip()

    print(output, end="\n\n")
    log_to_file(output)   

def log_tests_start():
    """Logs the header and metadata at the beginning of the test run."""
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")    
    output = textwrap.dedent(f"""
    ...............................................................
    >>> RUNNING TEST-SUITE 'AUTHENTICATION'
    >>> Start: {start_time}
    >>> No. of Test Cases: {len(test_cases)}
    ...............................................................    
    """).strip()
   
    print("\n" + output, end="\n\n")     
    log_to_file(output, True)       

def log_tests_finished(all_assertions_met: bool):
    """Logs the final summary of the test suite."""
    status_msg = "SUCCESS" if all_assertions_met else "FAILED"
    
    output = textwrap.dedent(f"""
    ...............................................................
    >>> TEST-SUITE 'AUTHENTICATION' FINISHED: {status_msg}
    ...............................................................
    """).strip()
    
    print(output, end="\n\n")     
    log_to_file(output)              


def log_to_file(output, prepend_lb:bool = False):
    """Writes the output to the configured LOG_PATH."""
    if LOG != "1":
        return
    
    prefix = "\n" if prepend_lb else ""
    
    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(prefix + output + "\n\n")    

def main() -> int:
    """
    Main entry point for the test script.
    Coordinates initialization, execution, and exit codes.
    """    
    log_tests_start()
    
    # 1. Block execution until API is healthy - to ensure API is actually ready before running tests.
    if not wait_for_api():
        log_api_not_ready()
        return 1      
   
    # 2. Iterate through test cases
    all_assertions_met = True    
    for test_no, test_case in enumerate(test_cases, start=1):
        test_result = check_test_case(test_case)
        log_result(test_no, test_case, test_result)
        
        # If any single test fails, the entire suite is considered failed
        if not test_result.is_success:
            all_assertions_met = False

    # 3. Finalize
    log_tests_finished(all_assertions_met)    
    return 0 if all_assertions_met else 1
        
if __name__ == "__main__":
    # Raise SystemExit to ensure the return value of main() is used as the shell exit code
    raise SystemExit(main())   

        