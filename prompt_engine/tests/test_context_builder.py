from prompt_engine.app.context_builder import build_context


def test_build_context_formats_nested_payload() -> None:
    payload = {
        "application": "InventoryApp",
        "server": {"os": "Windows", "cpu": 4},
        "components": ["IIS", "SQL Server"],
    }

    result = build_context(payload)

    expected = (
        "## application\n"
        "InventoryApp\n\n"
        "## server\n"
        "- os: Windows\n"
        "- cpu: 4\n\n"
        "## components\n"
        "- IIS\n"
        "- SQL Server"
    )
    assert result == expected
