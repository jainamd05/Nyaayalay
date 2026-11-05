from openai import OpenAI

from .config import GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL, LLM_TIMEOUT_SECONDS


class LLMConfigurationError(RuntimeError):
    """The LLM provider is not configured (e.g. missing API key)."""


def get_llm_client() -> OpenAI:
    """Create a Groq client using Groq's OpenAI-compatible API."""
    if not GROQ_API_KEY:
        raise LLMConfigurationError(
            "GROQ_API_KEY is not configured. Add it to your .env file "
            "(locally) or to the service's environment variables (Render)."
        )

    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=2,
    )


def get_llm_model() -> str:
    return LLM_MODEL
