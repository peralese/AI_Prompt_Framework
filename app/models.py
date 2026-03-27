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
