"""Reusable dataset loading utilities for experiments."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationDataset


class DatasetNotFoundError(FileNotFoundError):
    """Raised when a dataset file cannot be located."""


class DatasetLoader:
    """Load reusable evaluation datasets from disk."""

    def load(self, dataset_path: str | Path) -> tuple[EvaluationDataset, Path]:
        """Return a dataset model and its resolved path."""

        resolved_path = Path(dataset_path).resolve()
        if not resolved_path.exists():
            raise DatasetNotFoundError(f"Dataset not found at '{resolved_path}'.")

        data = json.loads(resolved_path.read_text(encoding="utf-8"))
        dataset = EvaluationDataset.model_validate(data)
        return dataset, resolved_path
