"""Convert structured payloads into deterministic markdown context."""

from __future__ import annotations

from typing import Any


def build_context(data: dict[str, Any]) -> str:
    """Render a dictionary into markdown-style sections."""

    sections: list[str] = []
    for key, value in data.items():
        sections.append(f"## {key}\n{_render_value(value)}")
    return "\n\n".join(sections).strip()


def _render_value(value: Any, indent: int = 0) -> str:
    prefix = "  " * indent

    if isinstance(value, dict):
        lines: list[str] = []
        for key, nested_value in value.items():
            if isinstance(nested_value, (dict, list)):
                lines.append(f"{prefix}- {key}:")
                lines.append(_render_value(nested_value, indent + 1))
            else:
                lines.append(f"{prefix}- {key}: {nested_value}")
        return "\n".join(lines) if lines else f"{prefix}- null"

    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_render_value(item, indent + 1))
            else:
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines) if lines else f"{prefix}- null"

    if value is None:
        return "null"

    return str(value)
