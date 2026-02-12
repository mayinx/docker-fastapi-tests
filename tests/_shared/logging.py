# tests/_shared/logging.py
import datetime
import os
import textwrap
from .config import Config
from .params import iter_params

from tests._shared.types import TestCase, TestResult

def ensure_log_dir(cfg: Config) -> None:
    # Only create directories when file logging is enabled
    if cfg.log != "1":
        return
    log_dir = os.path.dirname(cfg.log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

def log_to_file(cfg: Config, output: str, prepend_lb: bool = False) -> None:
    # Append to the shared log file only when LOG="1"
    if cfg.log != "1":
        return

    prefix = "\n" if prepend_lb else ""

    try:
        with open(cfg.log_path, "a", encoding="utf-8") as f:
            f.write(prefix + output + "\n\n")
    except PermissionError as e:
        print(
            f'WARN: Could not write log file (permission denied): "{cfg.log_path}". '
            f"Details: {e}"
        )
    except OSError as e:
        print(
            f'WARN: Could not write log file (OS error): "{cfg.log_path}". '
            f"Details: {e}"
        )

def log_suite_start(cfg: Config, suite_name: str, num_cases: int) -> None:
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = textwrap.dedent(f"""
    ...............................................................
    >>> RUNNING TEST-SUITE '{suite_name}'
    >>> Start: {start_time}
    >>> No. of Test Cases: {num_cases}
    ...............................................................
    """).strip()

    print("\n" + output, end="\n\n")
    log_to_file(cfg, output, prepend_lb=True)

def log_suite_finished(cfg: Config, suite_name: str, success: bool) -> None:
    status_msg = "SUCCESS" if success else "FAILED"
    output = textwrap.dedent(f"""
    ...............................................................
    >>> TEST-SUITE '{suite_name}' FINISHED: {status_msg}
    ...............................................................
    """).strip()

    print(output, end="\n\n")
    log_to_file(cfg, output)

def log_api_not_ready(cfg: Config, suite_name: str) -> None:
    output = textwrap.dedent(f"""
    ==========================================
        TEST-SUITE '{suite_name}' ABORTED
    ==========================================
    API readiness check FAILED
    expected /status => "1"
    ==> TEST STATUS: FAILURE
    """).strip()

    print(output, end="\n\n")
    log_to_file(cfg, output)

def log_result(cfg: Config, suite_name: str, test_no: int, test_case: TestCase, test_result: TestResult):
    """
    Formats and writes ONE test result to stdout and (if LOG="1") appends it to the shared log file.

    Important: request params are rendered dynamically via iter_params(test_case.params),
    so suites can have different TestParams fields without changing this logger.
    """

    # 1) Render request params dynamically (works for any TestParams shape)
    params_lines = "\n".join(f'| {k}="{v}"' for k, v in iter_params(test_case.params))

    # 2) Optional: show expected sentiment + actual score (only if this testcase defines it)
    score_block = ""
    expected_score = getattr(test_case, "expected_score", None)
    if expected_score is not None:
        actual_score = "n/a" if test_result.score is None else test_result.score
        score_block = (
            f"\n- Expected sentiment = {expected_score}"
            f"\n- Actual score = {actual_score}"
        )

    # 3) Assemble the report block (kept stable across suites for easy scanning)
    output = f"""==========================================
    {suite_name} TEST NO. {test_no}
==========================================
Request done at "{test_case.api_url}"
Request Params:
{params_lines}
Expected vs Actual:
- Expected status code = {test_case.expected_code}
- Actual status code = {test_result.status_code}{score_block}
==> TEST STATUS: {test_result.test_status}""".strip()

    # write log to console and optionally to the shared log file 
    print(output, end="\n\n")
    log_to_file(cfg, output)     