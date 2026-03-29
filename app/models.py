"""Lightweight data models used by the prompt engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Input required to execute a prompt."""

    category: str
    template_name: str
    input_payload: dict[str, Any]
    system_prompt: str | None = None
    require_json_output: bool = False
    required_keys: list[str] = Field(default_factory=list)


class PromptResponse(BaseModel):
    """Prompt execution result."""

    template_path: str
    rendered_prompt: str
    raw_output: str
    parsed_output: dict[str, Any] | None = None
    model: str


class EvaluationResult(BaseModel):
    """Single evaluation record saved to disk."""

    prompt_name: str
    input_payload: dict[str, Any]
    output_text: str
    notes: str | None = None
    score: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExperimentConfig(BaseModel):
    """Configuration for running a prompt comparison experiment."""

    experiment_name: str
    templates: list[str]
    input_file: str | None = None
    dataset_file: str | None = None
    expects_json: bool = False
    required_keys: list[str] = Field(default_factory=list)


class ExperimentRunResult(BaseModel):
    """Single experiment run result for one template/input pair."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    experiment_name: str
    template_name: str
    input_file: str
    dataset_name: str | None = None
    case_id: str | None = None
    case_description: str | None = None
    raw_output: str | None = None
    validation_status: str
    validation_error: str | None = None
    run_status: str = "completed"
    run_error: str | None = None
    model: str | None = None
    template_path: str | None = None


class DatasetCase(BaseModel):
    """Single reusable evaluation case."""

    case_id: str
    input_payload: dict[str, Any]
    description: str | None = None
    notes: str | None = None


class EvaluationDataset(BaseModel):
    """Reusable dataset for prompt experiments."""

    dataset_name: str
    category: str | None = None
    cases: list[DatasetCase]
