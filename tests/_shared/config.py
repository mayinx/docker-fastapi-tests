# tests/_shared/config.py
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    api_address: str
    api_port: int
    log: str
    log_path: str
    timeout: float

def load_config() -> Config:
    return Config(
        api_address=os.environ.get("API_ADDRESS", "api"),
        api_port=int(os.environ.get("API_PORT", "8000")),
        log=os.environ.get("LOG", "0"),
        log_path=os.environ.get("LOG_PATH", "/shared/api_test.log"),
        timeout=float(os.environ.get("HTTP_TIMEOUT", "5")),
    )
