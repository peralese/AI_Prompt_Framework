"""Prompt template loading utilities."""

from __future__ import annotations

from pathlib import Path


class TemplateNotFoundError(FileNotFoundError):
    """Raised when a prompt template cannot be located."""


class TemplateLoader:
    """Load prompt templates from the prompts directory."""

    def __init__(self, prompts_dir: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.prompts_dir = Path(prompts_dir) if prompts_dir else base_dir / "prompts"

    def load(self, category: str, template_name: str) -> tuple[str, str]:
        """Return the template text and resolved file path."""

        template_path = self.prompts_dir / category / f"{template_name}.txt"
        if not template_path.exists():
            raise TemplateNotFoundError(
                f"Template not found for category='{category}', template='{template_name}' "
                f"at '{template_path}'."
            )

        return template_path.read_text(encoding="utf-8").strip(), str(template_path)
