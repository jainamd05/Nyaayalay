import json
import re

from openai import APIError, APITimeoutError, OpenAI
from pydantic import BaseModel, ValidationError

from .config import (
    GROQ_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_RETRIES,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
)


class LLMError(RuntimeError):
    """Raised when the LLM provider fails or returns unusable output."""


_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Create (once) a Groq client using Groq's OpenAI-compatible API."""
    global _client

    if not GROQ_API_KEY:
        raise LLMError(
            "GROQ_API_KEY is not configured. Add it to your .env file "
            "(or to the environment variables of your hosting provider)."
        )

    if _client is None:
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=LLM_BASE_URL,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=2,
        )
    return _client


def _extract_json(text: str) -> str:
    """Strip code fences or surrounding prose and return the JSON object text."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text


def call_structured(
    schema: type[BaseModel],
    system_prompt: str,
    user_prompt: str,
):
    """
    Call the LLM and force the response to follow the supplied Pydantic schema.

    This keeps the same interface used by router.py, extraction.py,
    classification.py, and verification.py.
    """

    client = get_client()

    messages = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n\n"
                "You must respond ONLY with a single valid JSON object. "
                "Do not include markdown, explanations outside the JSON, "
                "or code fences. Confidence values are decimals between 0 and 1.\n\n"
                "The JSON object must follow this JSON schema:\n"
                f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
            ),
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    last_error: Exception | None = None

    for _ in range(LLM_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                temperature=0,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except APITimeoutError as exc:
            raise LLMError("The language model timed out. Please try again.") from exc
        except APIError as exc:
            # Groq rejects json_object responses that fail its own JSON check
            # with a 400 "json_validate_failed"; that is worth retrying.
            if "json_validate_failed" in str(exc):
                last_error = exc
                continue
            raise LLMError(f"The language model request failed: {exc}") from exc

        text = response.choices[0].message.content
        if not text:
            last_error = LLMError("Groq returned an empty structured response.")
            continue

        try:
            return schema.model_validate_json(_extract_json(text))
        except ValidationError as exc:
            last_error = exc
            continue

    raise LLMError(
        f"The language model returned invalid structured output: {last_error}"
    ) from last_error


def pretty_json(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump()

    return json.dumps(value, indent=2, ensure_ascii=False)
