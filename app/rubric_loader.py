"""Reusable rubric loading utilities for experiments."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationRubric


class RubricNotFoundError(FileNotFoundError):
    """Raised when a rubric file cannot be located."""


class RubricLoader:
    """Load reusable scoring rubrics from disk."""

    def load(self, rubric_path: str | Path) -> tuple[EvaluationRubric, Path]:
        """Return a rubric model and its resolved path."""

        resolved_path = Path(rubric_path).resolve()
        if not resolved_path.exists():
            raise RubricNotFoundError(f"Rubric not found at '{resolved_path}'.")

        data = json.loads(resolved_path.read_text(encoding="utf-8"))
        rubric = EvaluationRubric.model_validate(data)
        return rubric, resolved_path
