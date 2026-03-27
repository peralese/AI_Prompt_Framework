"""Simple evaluation logging harness."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationResult


class Evaluator:
    """Persist prompt evaluation records to JSONL."""

    def __init__(self, log_dir: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.log_dir = Path(log_dir) if log_dir else base_dir / "evaluation_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def save_result(
        self,
        prompt_name: str,
        input_payload: dict,
        output_text: str,
        notes: str | None = None,
        score: float | None = None,
    ) -> Path:
        """Append an evaluation result to a JSONL file."""

        result = EvaluationResult(
            prompt_name=prompt_name,
            input_payload=input_payload,
            output_text=output_text,
            notes=notes,
            score=score,
        )
        output_path = self.log_dir / f"{prompt_name}.jsonl"
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result.model_dump(mode="json")) + "\n")
        return output_path
