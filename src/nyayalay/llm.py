from openai import OpenAI

from .config import GROQ_API_KEY, LLM_MODEL


def get_llm_client() -> OpenAI:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to your .env file."
        )

    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )


def get_llm_model() -> str:
    return LLM_MODEL