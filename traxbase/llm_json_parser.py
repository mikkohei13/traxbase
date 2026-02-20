import json
import re


EXPECTED_FIELDS = ("variation_concept", "artistic_style", "color_palette")
MAX_FIELD_LENGTH = 256

FALLBACK_DEFAULTS = {
    "variation_concept": "color gradient",
    "artistic_style": "digital illustration",
    "color_palette": "saturated monochrome",
}

NON_JSON_DEFAULTS = {
    "artistic_style": "digital illustration",
    "color_palette": "saturated monochrome",
}


def parse_image_prompt_json(raw_text: str | None) -> dict:
    """Parse LLM output into a dict with variation_concept, artistic_style, and color_palette.

    Handles markdown code fences, malformed JSON, missing/extra fields,
    non-string values, and complete fallback when the response isn't JSON at all.
    Returns FALLBACK_DEFAULTS if raw_text is empty or None.
    """
    if not raw_text or not raw_text.strip():
        return dict(FALLBACK_DEFAULTS)

    text = raw_text.strip()
    text = _strip_markdown_fence(text)

    parsed = _try_parse_json(text)
    if isinstance(parsed, dict):
        return _normalize_fields(parsed)

    return {
        "variation_concept": text[:MAX_FIELD_LENGTH],
        **NON_JSON_DEFAULTS,
    }


def _strip_markdown_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def _try_parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    try:
        fixed = text.replace("'", '"')
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError):
        return None


def _normalize_fields(data: dict) -> dict:
    result = {}
    for field in EXPECTED_FIELDS:
        value = data.get(field)
        if value is None or not isinstance(value, str):
            value = str(value) if value is not None else ""
        value = value.strip()[:MAX_FIELD_LENGTH]
        result[field] = value
    return result
