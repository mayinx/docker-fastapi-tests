# tests/_shared/readiness.py
import time
import requests
from .config import Config

def wait_for_api(cfg: Config, timeout_s: int = 40) -> bool:
    url = f"http://{cfg.api_address}:{cfg.api_port}/status"
    start = time.time()

    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=cfg.timeout)
            if r.status_code == 200 and r.text.strip() == "1":
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

    return False
