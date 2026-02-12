# tests/_shared/config.py
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    # Where the API is reachable from INSIDE docker-compose network ("api" by default)
    api_address: str
    # API port (container port, usually 8000)
    api_port: int
    # LOG="1" => write to shared log file; anything else => console-only
    log: str
    # Shared log file path (bind-mounted via ./shared:/shared)
    log_path: str
    # HTTP request timeout (seconds) for requests.get(...)
    timeout: float

def load_config() -> Config:
    # Keep all suites consistent by reading env vars in ONE place.
    return Config(
        api_address=os.environ.get("API_ADDRESS", "api"),
        api_port=int(os.environ.get("API_PORT", "8000")),
        log=os.environ.get("LOG", "0"),
        log_path=os.environ.get("LOG_PATH", "/shared/api_test.log"),
        timeout=float(os.environ.get("HTTP_TIMEOUT", "5")),
    )
