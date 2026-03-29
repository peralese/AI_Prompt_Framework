import json
from pathlib import Path

import pytest

from app.rubric_loader import RubricLoader, RubricNotFoundError


def test_rubric_loader_reads_rubric(tmp_path: Path) -> None:
    rubric_path = tmp_path / "rubric.json"
    rubric_path.write_text(
        json.dumps(
            {
                "rubric_name": "summary_rubric",
                "category": "summarization",
                "criteria": [
                    {
                        "criterion_id": "non_empty_output",
                        "description": "Output must not be empty.",
                        "rule_type": "non_empty_output",
                        "weight": 1.0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rubric, resolved_path = RubricLoader().load(rubric_path)

    assert rubric.rubric_name == "summary_rubric"
    assert rubric.criteria[0].criterion_id == "non_empty_output"
    assert resolved_path == rubric_path.resolve()


def test_rubric_loader_raises_for_missing_rubric(tmp_path: Path) -> None:
    with pytest.raises(RubricNotFoundError):
        RubricLoader().load(tmp_path / "missing.json")
