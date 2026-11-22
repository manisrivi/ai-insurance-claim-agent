# llm.py: gives the app an AI "brain", with automatic fallback to a backup brain
from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings

# Model names in one place (fixed names = predictable behaviour in production)
GEMINI_MODEL = "gemini-3.5-flash-lite"
CLAUDE_MODEL = "claude-haiku-5-5"


def _make_gemini():
    # Gemini with a timeout and retries
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=settings.google_api_key,
        timeout=60,
        max_retries=2,
    )


def _make_claude():
    # Claude with a timeout and retries
    return ChatAnthropic(
        model=CLAUDE_MODEL,
        api_key=settings.anthropic_api_key,
        timeout=60,
        max_retries=2,
    )


@lru_cache
def _primary_and_backups():
    # Only use brains whose API key exists in .env
    makers = {}
    if settings.google_api_key:
        makers["gemini"] = _make_gemini
    if settings.anthropic_api_key:
        makers["claude"] = _make_claude
    if not makers:
        raise RuntimeError("No LLM API key found. Add GOOGLE_API_KEY or ANTHROPIC_API_KEY to .env")

    # Main brain = LLM_PROVIDER from .env; the rest become backups
    primary_name = settings.llm_provider if settings.llm_provider in makers else next(iter(makers))
    primary = makers.pop(primary_name)()
    backups = tuple(make() for make in makers.values())
    return primary, backups


@lru_cache
def get_llm():
    # A normal chat brain; switches to the backup automatically if the main one fails
    primary, backups = _primary_and_backups()
    if backups:
        return primary.with_fallbacks(list(backups))
    return primary


@lru_cache
def get_structured_llm(schema):
    # A brain that must answer in the shape of a Pydantic schema (like filling a form)
    primary, backups = _primary_and_backups()
    structured = primary.with_structured_output(schema)
    if backups:
        return structured.with_fallbacks(
            [backup.with_structured_output(schema) for backup in backups]
        )
    return structured