# tests/_shared/logging.py
import datetime
import os
import textwrap
from .config import Config

def ensure_log_dir(cfg: Config) -> None:
    if cfg.log != "1":
        return
    log_dir = os.path.dirname(cfg.log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

def log_to_file(cfg: Config, output: str, prepend_lb: bool = False) -> None:
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
