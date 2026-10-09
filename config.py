import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env relative to project root
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

@dataclass(frozen=True)
class Settings:
    """Centralized, typed application configuration."""
    database_url: str = os.getenv("DATABASE_URL", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    allow_synthetic_seed: bool = os.getenv("ALLOW_SYNTHETIC_SEED", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    calendar_api_base: str = os.getenv(
        "CALENDAR_API_BASE", 
        "https://calendar-api-d7a8.onrender.com/v1/holidays"
    )

    def validate(self):
        """Fail fast at startup if critical configuration is missing."""
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL must be set in environment or .env file."
            )

settings = Settings()
# Validate eagerly when config is imported
settings.validate()
