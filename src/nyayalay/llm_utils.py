from google import genai
from google.genai import types
from pydantic import BaseModel
from .config import GEMINI_API_KEY, GEMINI_MODEL

def get_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to .env.")
    return genai.Client(api_key=GEMINI_API_KEY)

def call_structured(schema: type[BaseModel], system_prompt: str, user_prompt: str):
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
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, schema):
        return parsed
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty structured response.")
    try:
        return schema.model_validate_json(text)
    except Exception as exc:
        raise RuntimeError(f"Gemini returned invalid structured output: {text}") from exc

def pretty_json(value) -> str:
    import json
    if isinstance(value, BaseModel):
        value = value.model_dump()
    return json.dumps(value, indent=2, ensure_ascii=False)
