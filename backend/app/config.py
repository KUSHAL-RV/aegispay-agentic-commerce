"""AegisPay configuration module using pydantic-settings with standard pydantic fallback."""

import os
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel
    class BaseSettings(BaseModel):
        """Fallback settings class when pydantic-settings is not installed."""
        def __init__(self, **values):
            env_vals = {}
            for field in self.model_fields.keys():
                if field in os.environ:
                    env_vals[field] = os.environ[field]
            env_vals.update(values)
            super().__init__(**env_vals)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_MODE: str = "sandbox"
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"

    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    DATABASE_URL: str = "sqlite:///./aegispay.db"

    ED25519_PRIVATE_KEY: str = ""
    ED25519_PUBLIC_KEY: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
