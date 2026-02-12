# tests/_shared/readiness.py
import time
import requests
from .config import Config

def wait_for_api(cfg: Config, timeout_s: int = 40) -> bool:
    # Compose "depends_on" is NOT a readiness check — we actively poll /status here.
    url = f"http://{cfg.api_address}:{cfg.api_port}/status"
    print(f"# Waiting for API readiness at {url} (timeout: {timeout_s}s)")
  
    start = time.time()
    last_msg = 0.0    

    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=cfg.timeout)
            if r.status_code == 200 and r.text.strip() == "1":
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        
        # Small heartbeat every ~5s so it doesn't feel frozen
        elapsed = time.time() - start
        if elapsed - last_msg >= 5:
            print(f"# ...still waiting ({int(elapsed)}s)")
            last_msg = elapsed

    print("# API readiness check timed out.")
    return False
