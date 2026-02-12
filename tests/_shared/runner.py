# tests/_shared/runner.py
from __future__ import annotations # Keep type hints as strings (lazy evaluation) to avoid forward-ref/circular-import issues.
import requests
from .config import Config
from .params import  params_dict
from .types import TestCase, TestResult

def run_test_case(cfg: Config, test_case: TestCase) -> TestResult:
    """
    Runs ONE HTTP GET test case against the API and evaluates:

    - Request params: uses params_dict(test_case.params) so this stays generic for any TestParams shape.
    - Always checks the expected HTTP status code.
    - Optionally checks sentiment (score sign) when test_case.expected_score is set ("positive"/"negative").

    Returns a TestResult including status_code, SUCCESS/FAILURE, and (if parsed) the score.
    """
    try: 
        # 1) Execute request against the API endpoint for this testcase
        response = requests.get(
            url=f"http://{cfg.api_address}:{cfg.api_port}{test_case.api_url}",
            params=params_dict(test_case.params),
            timeout=cfg.timeout,
        )  
        
        # 2) Always validate HTTP status code - compare actual HTTP code vs the one defined in the TestCase
        status_ok = response.status_code == test_case.expected_code   
        
        # 3) Optional: validate sentiment direction (only for CONTENT testcases)
        # Default is "ok" so non-content suites don't need special handling.
        score_ok = True      
        score=None    
      
        # Sentiment/score test? Extract score and compare against expectation
        if test_case.expected_score is not None:
            # API returns JSON like: {"score": <float>}
            data = response.json()
            raw_score = data.get("score", None)         
            
            # If score is missing/unparseable, treat as failure (content check can't be evaluated)
            try:
                score = float(raw_score)
            except (TypeError, ValueError):
                score_ok = False
            else:
                # Note: score can be any float (e.g. -0.66, +0.75) — we only check the sign.
                if test_case.expected_score == "positive":
                    score_ok = score > 0
                elif test_case.expected_score == "negative":
                    score_ok = score < 0
                else:
                    # Unknown expectation keyword => fail loudly (signals a bad testcase definition)
                    score_ok = False

        # 4) Overall success is the conjunction of all checks
        is_success = status_ok and score_ok

        return TestResult(
            is_success=is_success, 
            status_code=response.status_code, 
            test_status="SUCCESS" if is_success else "FAILURE",    
            score=score # present for content tests; otherwise None
        )
    except requests.exceptions.RequestException as e:
        # Handle Network/HTTP-layer failures (timeout, connection refused, DNS issues, etc.)
        return TestResult(
            is_success=False,
            status_code=0, # 0 => no HTTP response received
            test_status=f"ERROR: {type(e).__name__}",
            score=None
        )    

