from typing import Type, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from .config import GEMINI_API_KEY, GEMINI_MODEL

T = TypeVar("T", bound=BaseModel)


def get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file."
        )

    return genai.Client(api_key=GEMINI_API_KEY)


def call_structured(
    schema: Type[T],
    system_prompt: str,
    user_prompt: str,
) -> T:
    """
    Call Gemini and force the response into the supplied Pydantic schema.

    Google Gemini supports structured JSON output with Pydantic schemas.
    This is especially useful for Nyayalay because router/extraction/
    classification/verification all need predictable machine-readable output.
    """
    client = get_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        return schema.model_validate_json(response.text)
    except Exception as exc:
        raise RuntimeError(
            f"Gemini returned invalid structured output: {response.text}"
        ) from exc


def pretty_json(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump()
    import json
    return json.dumps(value, indent=2, ensure_ascii=False)
