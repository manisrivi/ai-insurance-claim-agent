# Reads settings from .env (like process.env, but with types + checks)
import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# In production, the officer key must be at least this long (random, not a word)
MIN_PROD_OFFICER_KEY_LENGTH = 24


class Settings(BaseSettings):
    # Load from the .env file; ignore extra lines we don't use
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" or "production" (production hides API docs and needs a strong officer key)
    environment: str = "development"

    # Which LLM brain: "gemini" or "claude"
    llm_provider: str = "gemini"
    # API keys (empty default so the app can still start)
    google_api_key: str = ""
    anthropic_api_key: str = ""

    # Supabase connection: REQUIRED (no default, so the app stops if it's missing)
    database_url: str

    # Business rule: claims above this amount need an officer
    officer_review_limit: float = 50000

    # Secret key officers send in the X-Officer-Key header (empty = officer API off)
    officer_api_key: str = ""

    # ChromaDB: "local" = folder on this machine (no account), "cloud" = Chroma Cloud (shared, managed)
    chroma_mode: str = "local"
    chroma_api_key: str = ""
    chroma_tenant: str = ""
    chroma_database: str = ""

    # Websites allowed to call this API (comma separated), e.g. https://claimcare.vercel.app
    cors_origins: str = "http://localhost:3000"

    # Rate limits per IP address, per minute
    rate_limit_submit_per_min: int = 5
    rate_limit_read_per_min: int = 60
    rate_limit_officer_per_min: int = 60

    # LangSmith tracing (optional)
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "insurance-claim-agent"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def officer_key_ok(self) -> bool:
        # No key = officer API off. In production a short key is refused too.
        if not self.officer_api_key:
            return False
        if self.is_production and len(self.officer_api_key) < MIN_PROD_OFFICER_KEY_LENGTH:
            return False
        return True


# One shared settings object for the whole app
settings = Settings()

if settings.officer_api_key and not settings.officer_key_ok:
    logger.warning("OFFICER_API_KEY is too short for production; the officer API is disabled.")

# LangSmith reads os.environ, but pydantic-settings does not write there. So we copy them.
if settings.langsmith_tracing and settings.langsmith_api_key:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
