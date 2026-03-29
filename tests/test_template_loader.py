from pathlib import Path

import pytest

from app.template_loader import TemplateLoader, TemplateNotFoundError


def test_template_loader_reads_template_text() -> None:
    loader = TemplateLoader()

    content, path = loader.load("classification", "software_classifier")

    assert "Return valid JSON only." in content
    assert path.endswith(str(Path("classification") / "software_classifier.txt"))


def test_template_loader_raises_for_missing_template() -> None:
    loader = TemplateLoader()

    with pytest.raises(TemplateNotFoundError):
        loader.load("classification", "missing_template")
