from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

@dataclass(frozen=True)
class Settings:
    app_name: str = "Email Verification Microservice"
    api_prefix: str = ""
    heybounce_api_key: str | None = os.getenv("HEYBOUNCE_API_KEY")
    heybounce_base_url: str = os.getenv("HEYBOUNCE_BASE_URL", "https://api.heybounce.io/v1").rstrip("/")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
    batch_max_emails: int = int(os.getenv("BATCH_MAX_EMAILS", "100"))
    provider_batch_max_emails: int = int(os.getenv("PROVIDER_BATCH_MAX_EMAILS", "25"))
    provider_rate_limit_per_minute: int = int(os.getenv("PROVIDER_RATE_LIMIT_PER_MINUTE", "500"))


settings = Settings()
