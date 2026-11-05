import json
import re

from pydantic import BaseModel, ValidationError

from .llm import LLMConfigurationError, get_llm_client, get_llm_model

__all__ = [
    "LLMConfigurationError",
    "LLMOutputError",
    "call_structured",
    "parse_structured",
    "pretty_json",
]

# How many extra attempts to make when the model returns JSON that does not
# match the expected schema. The validation error is fed back to the model.
MAX_REPAIR_ATTEMPTS = 1

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class LLMOutputError(RuntimeError):
    """The LLM returned output that could not be parsed into the schema."""


def _extract_json_text(text: str) -> str:
    """Strip markdown fences / surrounding prose and return the JSON object text."""
    text = _FENCE_RE.sub("", text.strip()).strip()
    if text.startswith("{"):
        return text
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_structured(schema: type[BaseModel], text: str | None) -> BaseModel:
    """
    Parse raw model output into `schema`.

    Handles common LLM quirks: code fences, prose around the JSON, and the
    object being wrapped in a single key such as {"RouteResult": {...}}.
    Raises `LLMOutputError` when the output cannot be validated.
    """
    if not text or not text.strip():
        raise LLMOutputError("The LLM returned an empty response.")

    try:
        data = json.loads(_extract_json_text(text))
    except json.JSONDecodeError as exc:
        raise LLMOutputError(f"The LLM did not return valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise LLMOutputError("The LLM returned JSON that is not an object.")

    fields = set(schema.model_fields)
    if len(data) == 1 and not (fields & set(data)):
        (inner,) = data.values()
        if isinstance(inner, dict):
            data = inner

    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise LLMOutputError(
            f"The LLM response did not match the {schema.__name__} schema: {exc}"
        ) from exc


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
    client = get_llm_client()

    messages = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n\n"
                "You must respond ONLY with a single valid JSON object. "
                "Do not include markdown, explanations outside the JSON, "
                "or code fences. Confidence values are decimals between 0 and 1.\n\n"
                "The JSON must follow this schema:\n"
                f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
            ),
        },
        {"role": "user", "content": user_prompt},
    ]

    last_error: LLMOutputError | None = None
    for _ in range(1 + MAX_REPAIR_ATTEMPTS):
        response = client.chat.completions.create(
            model=get_llm_model(),
            temperature=0,
            messages=messages,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content if response.choices else None

        try:
            return parse_structured(schema, text)
        except LLMOutputError as exc:
            last_error = exc
            messages = messages + [
                {"role": "assistant", "content": text or ""},
                {
                    "role": "user",
                    "content": (
                        "Your previous reply was rejected: "
                        f"{exc}\nReturn ONLY the corrected JSON object."
                    ),
                },
            ]

    raise last_error  # type: ignore[misc]


def pretty_json(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump()

    return json.dumps(value, indent=2, ensure_ascii=False)
