import json

from openai import OpenAI
from pydantic import BaseModel

from .config import GROQ_API_KEY, LLM_MODEL


def get_client() -> OpenAI:
    """Create a Groq client using Groq's OpenAI-compatible API."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to your .env file."
        )

    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )


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

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    f"{system_prompt}\n\n"
                    "You must respond ONLY with valid JSON. "
                    "Do not include markdown, explanations outside the JSON, "
                    "or code fences.\n\n"
                    "The JSON must follow this schema:\n"
                    f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content

    if not text:
        raise RuntimeError("Groq returned an empty structured response.")

    try:
        return schema.model_validate_json(text)
    except Exception as exc:
        raise RuntimeError(
            f"Groq returned invalid structured output: {text}"
        ) from exc


def pretty_json(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump()

    return json.dumps(value, indent=2, ensure_ascii=False)