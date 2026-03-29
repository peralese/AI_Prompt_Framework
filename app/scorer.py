"""Generic rubric-based scoring for experiment outputs."""

from __future__ import annotations

import json
from typing import Any

from .models import EvaluationRubric, ExperimentRunResult, RubricCriterion


class ScoringError(ValueError):
    """Raised when rubric scoring cannot be completed."""


class ExperimentScorer:
    """Score experiment runs using a reusable rubric."""

    def score_run(
        self,
        run_result: ExperimentRunResult,
        input_payload: dict[str, Any],
        rubric: EvaluationRubric,
    ) -> tuple[float, float, list[dict[str, Any]]]:
        """Return the earned score, max score, and per-criterion breakdown."""

        raw_output = (run_result.raw_output or "").strip()
        parsed_output = self._maybe_parse_json(raw_output)

        breakdown: list[dict[str, Any]] = []
        total_score = 0.0
        max_score = 0.0
        for criterion in rubric.criteria:
            criterion_passed = self._evaluate_criterion(
                criterion=criterion,
                run_result=run_result,
                raw_output=raw_output,
                parsed_output=parsed_output,
                input_payload=input_payload,
            )
            earned = criterion.weight if criterion_passed else 0.0
            max_score += criterion.weight
            total_score += earned
            breakdown.append(
                {
                    "criterion_id": criterion.criterion_id,
                    "description": criterion.description,
                    "rule_type": criterion.rule_type,
                    "weight": criterion.weight,
                    "passed": criterion_passed,
                    "score": earned,
                }
            )

        return total_score, max_score, breakdown

    def _evaluate_criterion(
        self,
        criterion: RubricCriterion,
        run_result: ExperimentRunResult,
        raw_output: str,
        parsed_output: Any,
        input_payload: dict[str, Any],
    ) -> bool:
        """Evaluate one rubric criterion."""

        rule_type = criterion.rule_type
        config = criterion.config

        if rule_type == "non_empty_output":
            return bool(raw_output)

        if rule_type == "validation_passed":
            return run_result.validation_status == "passed"

        if rule_type == "output_length_between":
            min_chars = int(config.get("min_chars", 0))
            max_chars = int(config.get("max_chars", 10**9))
            return min_chars <= len(raw_output) <= max_chars

        if rule_type == "contains_any_input_values":
            keys = config.get("input_keys", [])
            if not isinstance(keys, list):
                raise ScoringError("contains_any_input_values expects 'input_keys' as a list.")
            expected_values = self._collect_input_values(input_payload, keys)
            return any(value.lower() in raw_output.lower() for value in expected_values)

        if rule_type == "contains_all_strings":
            expected_strings = config.get("strings", [])
            if not isinstance(expected_strings, list):
                raise ScoringError("contains_all_strings expects 'strings' as a list.")
            return all(value.lower() in raw_output.lower() for value in expected_strings)

        if rule_type == "json_keys_present":
            required_keys = config.get("required_keys", [])
            if not isinstance(required_keys, list):
                raise ScoringError("json_keys_present expects 'required_keys' as a list.")
            if not isinstance(parsed_output, dict):
                return False
            return all(key in parsed_output for key in required_keys)

        raise ScoringError(f"Unsupported rubric rule type: {rule_type}")

    def _collect_input_values(
        self, input_payload: dict[str, Any], keys: list[str]
    ) -> list[str]:
        """Collect comparable string values from selected input keys."""

        values: list[str] = []
        for key in keys:
            if key not in input_payload:
                continue
            value = input_payload[key]
            if isinstance(value, str):
                values.append(value)
            elif isinstance(value, list):
                values.extend(str(item) for item in value if isinstance(item, (str, int, float)))
            elif isinstance(value, (int, float)):
                values.append(str(value))
        return [value for value in values if value]

    def _maybe_parse_json(self, raw_output: str) -> Any:
        """Parse JSON output when possible, otherwise return None."""

        if not raw_output:
            return None
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return None
