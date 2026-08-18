import base64
import json
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import ValidationError

from models import ExtractionResult

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"

MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

SYSTEM_PROMPT = """You are a work schedule extraction system. You will receive a photo of
a printed employee schedule. Extract ALL shifts into structured JSON.

The schedule may be in any format:
- Names in rows, dates in columns
- Names in columns, dates in rows
- A department name may appear as a header
- Times may be in 12h or 24h format
- Some cells may be empty (day off)
- Handwritten edits may appear over printed text

Return ONLY valid JSON in this exact format — no markdown, no backticks,
no explanation, just the JSON object:
{
  "department_name": "string or null",
  "schedule_period": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  },
  "shifts": [
    {
      "employee_name": "string",
      "date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "confidence": "high or low"
    }
  ]
}

Rules:
- Convert all times to 24-hour format (e.g., 2:00 PM → 14:00)
- If you cannot determine a specific date, include the raw column/row
  header in a "raw_date" field for that shift
- If a time is ambiguous or hard to read, set confidence to "low"
- Skip empty cells (days off) — do not create shift entries for them
- If you can identify the department name from a header, include it
- If you cannot determine the year, assume the current year"""


class ExtractionError(Exception):
    """Raised when Claude's response cannot be parsed into an ExtractionResult."""


def _media_type_for(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return MEDIA_TYPES.get(ext, "image/jpeg")


def _extract_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return match.group(1).strip() if match else text


def extract_schedule(image_bytes: bytes, filename: str) -> ExtractionResult:
    """Send a schedule photo to Claude Vision and return a validated ExtractionResult."""
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    media_type = _media_type_for(filename)

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Extract the schedule data from this image.",
                    },
                ],
            }
        ],
    )

    raw_text = response.content[0].text
    json_text = _extract_json(raw_text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Claude did not return valid JSON: {e}") from e

    try:
        return ExtractionResult.model_validate(data)
    except ValidationError as e:
        raise ExtractionError(f"Claude's response did not match the expected schema: {e}") from e
