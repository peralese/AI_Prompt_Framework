import json
from pathlib import Path

import pytest

from app.dataset_loader import DatasetLoader, DatasetNotFoundError


def test_dataset_loader_reads_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_name": "summary_dataset",
                "category": "summarization",
                "cases": [
                    {
                        "case_id": "case_1",
                        "description": "First case",
                        "input_payload": {"status": "In progress"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dataset, resolved_path = DatasetLoader().load(dataset_path)

    assert dataset.dataset_name == "summary_dataset"
    assert dataset.category == "summarization"
    assert dataset.cases[0].case_id == "case_1"
    assert resolved_path == dataset_path.resolve()


def test_dataset_loader_raises_for_missing_dataset(tmp_path: Path) -> None:
    with pytest.raises(DatasetNotFoundError):
        DatasetLoader().load(tmp_path / "missing.json")
