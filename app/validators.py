"""Helpers for validating model outputs."""

from __future__ import annotations

import json
import re


class ValidationError(ValueError):
    """Raised when output validation fails."""


def validate_json_output(text: str) -> dict:
    """Parse output text as JSON and ensure the root object is a dictionary."""

    normalized_text = _extract_json_candidate(text)

    try:
        data = json.loads(normalized_text)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON output: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValidationError("JSON output must be an object.")

    return data


def validate_required_keys(data: dict, required_keys: list[str]) -> bool:
    """Ensure all required keys are present in a JSON object."""

    if not isinstance(data, dict):
        raise ValidationError("Required-key validation expects a dictionary.")

    missing = [key for key in required_keys if key not in data]
    if missing:
        raise ValidationError(f"Missing required keys: {', '.join(missing)}")
    return True


def _extract_json_candidate(text: str) -> str:
    """Extract a likely JSON object from common model output formats."""

    stripped = text.strip()
    if not stripped:
        raise ValidationError("Invalid JSON output: response was empty.")

    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    object_match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if object_match:
        return object_match.group(0).strip()

    return stripped
