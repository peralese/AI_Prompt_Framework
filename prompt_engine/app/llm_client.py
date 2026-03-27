"""Provider-specific LLM client implementations."""

from __future__ import annotations

from openai import OpenAI
from openai import OpenAIError

from .config import get_settings
from .logger import get_logger


class LLMClientError(RuntimeError):
    """Raised when the LLM client cannot complete a request."""


class OpenAILLMClient:
    """Small wrapper around the OpenAI Responses API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.logger = get_logger(self.__class__.__name__, settings.log_level)

        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY is required to initialize the OpenAI client.")

        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text from the configured model."""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.responses.create(model=self.model, input=messages)
            output_text = response.output_text
        except OpenAIError as exc:
            self.logger.exception("OpenAI request failed.")
            raise LLMClientError(f"OpenAI request failed: {exc}") from exc
        except Exception as exc:  # pragma: no cover - defensive catch
            self.logger.exception("Unexpected LLM client failure.")
            raise LLMClientError(f"Unexpected LLM client failure: {exc}") from exc

        if not output_text:
            raise LLMClientError("LLM returned an empty response.")

        return output_text.strip()
