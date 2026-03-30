"""Generic rubric-based scoring for experiment outputs."""

from __future__ import annotations

import json
import re
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
            raw_score, note = self._score_criterion(
                criterion=criterion,
                run_result=run_result,
                raw_output=raw_output,
                parsed_output=parsed_output,
                input_payload=input_payload,
                rubric=rubric,
            )
            normalized_score = raw_score / criterion.scale_max if criterion.scale_max else 0.0
            earned = criterion.weight * normalized_score
            max_score += criterion.weight
            total_score += earned
            breakdown.append(
                {
                    "criterion_id": criterion.criterion_id,
                    "description": criterion.description,
                    "rule_type": criterion.rule_type,
                    "weight": criterion.weight,
                    "score": earned,
                    "max_score": criterion.weight,
                    "raw_score": raw_score,
                    "scale_max": criterion.scale_max,
                    "passed": raw_score >= criterion.scale_max,
                    "note": note,
                }
            )

        return total_score, max_score, breakdown

    def _score_criterion(
        self,
        criterion: RubricCriterion,
        run_result: ExperimentRunResult,
        raw_output: str,
        parsed_output: Any,
        input_payload: dict[str, Any],
        rubric: EvaluationRubric,
    ) -> tuple[int, str | None]:
        """Score one rubric criterion and return its raw score plus note."""

        rule_type = criterion.rule_type
        config = criterion.config

        if rule_type == "non_empty_output":
            return self._score_boolean(bool(raw_output), criterion.scale_max), None

        if rule_type == "validation_passed":
            return (
                self._score_boolean(
                    run_result.validation_status == "passed", criterion.scale_max
                ),
                None,
            )

        if rule_type == "output_length_between":
            min_chars = int(config.get("min_chars", 0))
            max_chars = int(config.get("max_chars", 10**9))
            passed = min_chars <= len(raw_output) <= max_chars
            note = None if passed else "Output length fell outside the preferred range."
            return self._score_boolean(passed, criterion.scale_max), note

        if rule_type == "contains_any_input_values":
            keys = config.get("input_keys", [])
            if not isinstance(keys, list):
                raise ScoringError("contains_any_input_values expects 'input_keys' as a list.")
            expected_values = self._collect_input_values(input_payload, keys)
            matched = any(value.lower() in raw_output.lower() for value in expected_values)
            note = None if matched else "The output did not surface core input context."
            return self._score_boolean(matched, criterion.scale_max), note

        if rule_type == "contains_all_strings":
            expected_strings = config.get("strings", [])
            if not isinstance(expected_strings, list):
                raise ScoringError("contains_all_strings expects 'strings' as a list.")
            matched = all(value.lower() in raw_output.lower() for value in expected_strings)
            note = None if matched else "The output missed one or more expected strings."
            return self._score_boolean(matched, criterion.scale_max), note

        if rule_type == "json_keys_present":
            required_keys = config.get("required_keys", [])
            if not isinstance(required_keys, list):
                raise ScoringError("json_keys_present expects 'required_keys' as a list.")
            matched = isinstance(parsed_output, dict) and all(
                key in parsed_output for key in required_keys
            )
            note = None if matched else "The output did not include the expected JSON keys."
            return self._score_boolean(matched, criterion.scale_max), note

        if rubric.category == "summarization":
            if rule_type == "summarization_executive_readability":
                return self._score_summarization_executive_readability(
                    raw_output, criterion
                )
            if rule_type == "summarization_structure_adherence":
                return self._score_summarization_structure_adherence(
                    raw_output, input_payload, criterion
                )
            if rule_type == "summarization_signal_to_noise":
                return self._score_summarization_signal_to_noise(
                    raw_output, input_payload, criterion
                )
            if rule_type == "summarization_risk_identification":
                return self._score_summarization_risk_identification(
                    raw_output, input_payload, criterion
                )
            if rule_type == "summarization_actionability":
                return self._score_summarization_actionability(
                    raw_output, input_payload, criterion
                )

        raise ScoringError(f"Unsupported rubric rule type: {rule_type}")

    def _score_summarization_executive_readability(
        self, raw_output: str, criterion: RubricCriterion
    ) -> tuple[int, str | None]:
        """Score how concise and executive-friendly a summary is."""

        if not raw_output:
            return 0, "The summary was empty."

        sentences = self._split_sentences(raw_output)
        sentence_count = len(sentences)
        avg_sentence_words = (
            sum(len(self._tokenize(sentence)) for sentence in sentences) / sentence_count
            if sentence_count
            else 0
        )
        technical_terms = [
            term.lower() for term in criterion.config.get("technical_terms", [])
        ]
        technical_hits = sum(raw_output.lower().count(term) for term in technical_terms)
        paragraphs = [part.strip() for part in raw_output.split("\n\n") if part.strip()]
        has_list_structure = any(
            line.strip().startswith(("- ", "* ", "1. ", "2. ", "3. "))
            for line in raw_output.splitlines()
        )

        score = 3
        notes: list[str] = []
        if len(raw_output) > 850 or sentence_count > 7:
            score = 1
            notes.append("Hard to scan quickly because the summary is too dense for an executive audience")
        elif len(raw_output) > 650 or sentence_count > 5:
            score = 2
            notes.append("Readable but still denser than an executive summary should be")
        elif len(raw_output) <= 420 and sentence_count <= 4:
            score = 4

        if avg_sentence_words > 30:
            score = min(score, 1)
            notes.append("Sentences are too long and make the summary difficult to read")
        elif avg_sentence_words > 24:
            score = min(score, 2)
            notes.append("Readable but could be tightened for faster scanning")
        elif avg_sentence_words <= 20 and score >= 4:
            score = max(score, 4)

        if technical_hits >= 5:
            score = max(1, score - 2)
            notes.append("Includes infrastructure detail that is not critical for executive audience")
        elif technical_hits >= 3:
            score = max(2, score - 1)
            notes.append("Leans technical in places for an executive-facing summary")

        if has_list_structure and sentence_count <= 4 and score >= 4:
            score = 5
        elif len(paragraphs) >= 2 and sentence_count <= 4 and score >= 4:
            score = 4
        elif score >= 4 and not (len(paragraphs) >= 2 or has_list_structure):
            notes.append("Readable but could be improved with clearer separation of risks and actions")

        return max(0, min(score, criterion.scale_max)), (
            None if not notes else self._format_notes(notes)
        )

    def _score_summarization_structure_adherence(
        self,
        raw_output: str,
        input_payload: dict[str, Any],
        criterion: RubricCriterion,
    ) -> tuple[int, str | None]:
        """Score whether the summary follows a structured executive format."""

        if not raw_output:
            return 0, "The summary was empty."

        lower_output = raw_output.lower()
        paragraphs = [part.strip() for part in raw_output.split("\n\n") if part.strip()]
        sentences = self._split_sentences(raw_output)
        first_sentence = sentences[0].lower() if sentences else ""
        status_value = str(input_payload.get("status", "")).lower()
        has_risk_language = any(
            keyword in lower_output for keyword in ["risk", "issue", "dependency", "uncertainty"]
        )
        has_action_language = any(
            keyword in lower_output for keyword in ["next", "action", "priority", "focus"]
        )
        has_list_structure = any(
            line.strip().startswith(("- ", "* ", "1. ", "2. ", "3. "))
            for line in raw_output.splitlines()
        )

        score = 3
        notes: list[str] = []
        if criterion.config.get("prefer_two_paragraphs") and len(paragraphs) == 2:
            score += 1
        elif criterion.config.get("prefer_two_paragraphs") and len(paragraphs) != 2:
            notes.append("Readable but could be improved with clearer separation of risks and actions")
        if criterion.config.get("status_first") and status_value and status_value not in first_sentence:
            score -= 2
            notes.append("Status is not surfaced early, so the summary takes longer to orient the reader")
        elif criterion.config.get("status_first") and status_value and status_value in first_sentence:
            score += 1
        if criterion.config.get("prefer_risks_and_actions") and not (
            has_risk_language and has_action_language
        ):
            score -= 1
            notes.append("Risks and next steps are present but not clearly separated")
        elif criterion.config.get("prefer_risks_and_actions") and (
            has_risk_language and has_action_language
        ):
            score += 1

        return max(0, min(score, criterion.scale_max)), (
            None if not notes else self._format_notes(notes)
        )

    def _score_summarization_signal_to_noise(
        self,
        raw_output: str,
        input_payload: dict[str, Any],
        criterion: RubricCriterion,
    ) -> tuple[int, str | None]:
        """Score whether the summary emphasizes important signal over detail."""

        if not raw_output:
            return 0, "The summary was empty."

        lower_output = raw_output.lower()
        preferred_keys = criterion.config.get(
            "preferred_input_keys", ["status", "highlights", "risks", "next_actions"]
        )
        signal_hits = 0
        for key in preferred_keys:
            if key in input_payload and self._references_input_value(lower_output, input_payload[key]):
                signal_hits += 1

        digit_count = sum(char.isdigit() for char in raw_output)
        acronym_hits = len(re.findall(r"\b[A-Z]{2,}\b", raw_output))
        technical_detail_hits = len(
            re.findall(
                r"\b(server|database|api|schema|mapping|deployment|pipeline|integration|latency)\b",
                lower_output,
            )
        )
        has_risk_language = any(
            keyword in lower_output for keyword in ["risk", "issue", "dependency", "uncertainty"]
        )
        has_action_language = any(
            keyword in lower_output for keyword in ["next", "action", "priority", "focus"]
        )
        has_list_structure = any(
            line.strip().startswith(("- ", "* ", "1. ", "2. ", "3. "))
            for line in raw_output.splitlines()
        )

        score = 3
        notes: list[str] = []
        if signal_hits <= 1:
            score = 1
            notes.append("Key business signal is buried or missing")
        elif signal_hits == 2:
            score = 3
        else:
            score = 4

        if has_risk_language and has_action_language and signal_hits >= 3:
            score += 1
        if has_list_structure and has_risk_language and has_action_language:
            score += 1

        if len(raw_output) > 850 or digit_count >= 12 or acronym_hits >= 5 or technical_detail_hits >= 5:
            score = min(score, 1)
            notes.append("Includes infrastructure detail that is not critical for executive audience")
        elif len(raw_output) > 650 or digit_count >= 8 or acronym_hits >= 3 or technical_detail_hits >= 3:
            score = min(score, 2)
            notes.append("Captures the main points but still carries some low-value detail")

        return max(0, min(score, criterion.scale_max)), (
            None if not notes else self._format_notes(notes)
        )

    def _score_summarization_risk_identification(
        self,
        raw_output: str,
        input_payload: dict[str, Any],
        criterion: RubricCriterion,
    ) -> tuple[int, str | None]:
        """Score whether risks from the input are surfaced clearly."""

        risks = input_payload.get(criterion.config.get("risk_input_key", "risks"), [])
        if not risks:
            return criterion.scale_max, None

        lower_output = raw_output.lower()
        risk_keywords = [
            keyword.lower()
            for keyword in criterion.config.get(
                "risk_keywords", ["risk", "issue", "dependency", "uncertainty"]
            )
        ]
        has_risk_language = any(keyword in lower_output for keyword in risk_keywords)
        matched_risk_terms = self._count_keyword_matches(risks, lower_output)

        if not has_risk_language and matched_risk_terms == 0:
            return 0, "Risk not clearly surfaced."
        if not has_risk_language or matched_risk_terms == 0:
            return 2, "Risks are only weakly reflected."
        if matched_risk_terms == 1:
            return 4, "Risks are present but could be emphasized more clearly."
        return criterion.scale_max, None

    def _score_summarization_actionability(
        self,
        raw_output: str,
        input_payload: dict[str, Any],
        criterion: RubricCriterion,
    ) -> tuple[int, str | None]:
        """Score whether next actions are surfaced clearly."""

        actions = input_payload.get(criterion.config.get("actions_input_key", "next_actions"), [])
        if not actions:
            return criterion.scale_max, None

        lower_output = raw_output.lower()
        action_keywords = [
            keyword.lower()
            for keyword in criterion.config.get(
                "action_keywords", ["next", "action", "priority", "focus"]
            )
        ]
        has_action_language = any(keyword in lower_output for keyword in action_keywords)
        matched_action_terms = self._count_keyword_matches(actions, lower_output)

        explicit_action_phrases = [
            "next step",
            "next steps",
            "immediate next step",
            "immediate next steps",
            "the team should",
            "should now",
            "priority is to",
            "focus is to",
        ]
        has_explicit_direction = any(phrase in lower_output for phrase in explicit_action_phrases)

        if not has_action_language and matched_action_terms == 0:
            return 1, "No clear next steps are surfaced."
        if not has_action_language:
            if matched_action_terms <= 1:
                return 2, "Next steps are only implied and need clearer direction."
            return 3, "Next steps are present but could be more explicit or prioritized."
        if matched_action_terms == 0:
            return 2, "Next steps are implied but not explicit."
        if matched_action_terms <= 2 and not has_explicit_direction:
            return 3, "Next steps are present but could be more explicit or prioritized."
        if matched_action_terms == 1:
            return 4, "Next steps are clear, but ownership or priority could be sharper."
        if not has_explicit_direction:
            return 4, "Next steps are present but could be more explicit or prioritized."
        return criterion.scale_max, None

    def _score_boolean(self, passed: bool, scale_max: int) -> int:
        """Return a full or zero score for a boolean criterion."""

        return scale_max if passed else 0

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

    def _references_input_value(self, lower_output: str, value: Any) -> bool:
        """Check whether an output references a value from the input."""

        if isinstance(value, str):
            return value.lower() in lower_output
        if isinstance(value, list):
            return any(str(item).lower() in lower_output for item in value)
        return str(value).lower() in lower_output

    def _count_keyword_matches(self, input_items: Any, lower_output: str) -> int:
        """Count how many input items have at least one keyword reflected in the output."""

        if not isinstance(input_items, list):
            return 0

        matches = 0
        for item in input_items:
            if not isinstance(item, str):
                continue
            keywords = self._extract_keywords(item)
            if any(keyword in lower_output for keyword in keywords):
                matches += 1
        return matches

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract lightweight keywords from a sentence for matching."""

        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "this",
            "have",
            "has",
            "been",
            "still",
            "into",
            "will",
            "could",
            "next",
        }
        tokens = [
            token
            for token in re.findall(r"[a-zA-Z]{4,}", text.lower())
            if token not in stop_words
        ]
        return tokens[:4]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into rough sentence units."""

        return [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""

        return re.findall(r"\b\w+\b", text)

    def _format_notes(self, notes: list[str]) -> str:
        """Return a readable note string without duplicate messages."""

        deduped: list[str] = []
        for note in notes:
            cleaned = note.strip().rstrip(".")
            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)
        return ". ".join(deduped).capitalize() + "." if deduped else ""

    def _maybe_parse_json(self, raw_output: str) -> Any:
        """Parse JSON output when possible, otherwise return None."""

        if not raw_output:
            return None
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return None
