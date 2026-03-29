import pytest

from app.validators import (
    ValidationError,
    validate_json_output,
    validate_required_keys,
)


def test_validate_json_output_returns_dict() -> None:
    result = validate_json_output('{"items": []}')

    assert result == {"items": []}


def test_validate_json_output_rejects_invalid_json() -> None:
    with pytest.raises(ValidationError):
        validate_json_output("not-json")


def test_validate_required_keys_raises_for_missing_keys() -> None:
    with pytest.raises(ValidationError):
        validate_required_keys({"items": []}, ["items", "summary"])


def test_validate_json_output_accepts_fenced_json() -> None:
    result = validate_json_output(
        '```json\n{"items": [{"name": "Redis"}]}\n```'
    )

    assert result == {"items": [{"name": "Redis"}]}


def test_validate_json_output_extracts_json_from_surrounding_text() -> None:
    result = validate_json_output(
        'Here is the result:\n{"items": [{"name": "Redis"}]}\nThanks.'
    )

    assert result == {"items": [{"name": "Redis"}]}
