from prompt_engine.app.models import PromptRequest
from prompt_engine.app.prompt_engine import PromptEngine
from prompt_engine.app.template_loader import TemplateLoader


class DummyLLMClient:
    def __init__(self) -> None:
        self.model = "dummy-model"
        self.last_prompt = None
        self.last_system_prompt = None

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        return '{"items": [{"name": "SQL Server", "category": "database", "reasoning": "Named as a database server."}]}'


def test_prompt_engine_injects_context_and_validates_json() -> None:
    client = DummyLLMClient()
    engine = PromptEngine(template_loader=TemplateLoader(), llm_client=client)
    request = PromptRequest(
        category="classification",
        template_name="software_classifier",
        input_payload={"components": ["SQL Server"]},
        system_prompt="Respond carefully.",
        require_json_output=True,
        required_keys=["items"],
    )

    response = engine.run(request)

    assert "## components\n- SQL Server" in client.last_prompt
    assert client.last_system_prompt == "Respond carefully."
    assert response.parsed_output == {
        "items": [
            {
                "name": "SQL Server",
                "category": "database",
                "reasoning": "Named as a database server.",
            }
        ]
    }
    assert response.model == "dummy-model"
