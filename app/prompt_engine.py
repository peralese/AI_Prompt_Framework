"""Main prompt engine orchestration."""

from __future__ import annotations

from .config import get_settings
from .context_builder import build_context
from .llm_client import OpenAILLMClient
from .logger import get_logger
from .models import PromptRequest, PromptResponse
from .template_loader import TemplateLoader
from .validators import validate_json_output, validate_required_keys


class PromptEngine:
    """Coordinate template loading, context rendering, and LLM execution."""

    def __init__(
        self,
        template_loader: TemplateLoader | None = None,
        llm_client: OpenAILLMClient | None = None,
    ) -> None:
        settings = get_settings()
        self.template_loader = template_loader or TemplateLoader()
        self.llm_client = llm_client or OpenAILLMClient()
        self.logger = get_logger(self.__class__.__name__, settings.log_level)
        self.model = getattr(self.llm_client, "model", settings.openai_model)

    def run(self, request: PromptRequest) -> PromptResponse:
        """Execute a prompt request and optionally validate JSON output."""

        template_text, template_path = self.template_loader.load(
            request.category, request.template_name
        )
        context = build_context(request.input_payload)
        rendered_prompt = template_text.replace("{{context}}", context)

        self.logger.info(
            "Running template '%s/%s'.", request.category, request.template_name
        )
        raw_output = self.llm_client.generate(
            prompt=rendered_prompt,
            system_prompt=request.system_prompt,
        )

        parsed_output = None
        if request.require_json_output:
            parsed_output = validate_json_output(raw_output)
            if request.required_keys:
                validate_required_keys(parsed_output, request.required_keys)

        return PromptResponse(
            template_path=template_path,
            rendered_prompt=rendered_prompt,
            raw_output=raw_output,
            parsed_output=parsed_output,
            model=self.model,
        )
