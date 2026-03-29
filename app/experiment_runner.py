"""Generic prompt experiment runner for comparing template variants."""

from __future__ import annotations

import json
from pathlib import Path

from .evaluator import Evaluator
from .logger import get_logger
from .models import ExperimentConfig, ExperimentRunResult, PromptRequest
from .prompt_engine import PromptEngine
from .validators import ValidationError, validate_json_output, validate_required_keys


class ExperimentRunner:
    """Run a reusable prompt comparison experiment across multiple templates."""

    def __init__(
        self,
        prompt_engine: PromptEngine | None = None,
        evaluator: Evaluator | None = None,
    ) -> None:
        self.prompt_engine = prompt_engine or PromptEngine()
        self.evaluator = evaluator or Evaluator()
        self.logger = get_logger(self.__class__.__name__)

    def load_config(self, config_path: str | Path) -> tuple[ExperimentConfig, Path]:
        """Load and validate an experiment config file."""

        resolved_config_path = Path(config_path).resolve()
        config_data = json.loads(resolved_config_path.read_text(encoding="utf-8"))
        config = ExperimentConfig.model_validate(config_data)
        return config, resolved_config_path

    def run_from_config(self, config_path: str | Path) -> list[ExperimentRunResult]:
        """Load an experiment config and execute its template runs."""

        config, resolved_config_path = self.load_config(config_path)
        return self.run_experiment(config, resolved_config_path.parent)

    def run_experiment(
        self,
        config: ExperimentConfig,
        base_dir: str | Path | None = None,
    ) -> list[ExperimentRunResult]:
        """Execute all template runs defined in an experiment config."""

        base_path = Path(base_dir).resolve() if base_dir else Path.cwd()
        input_path = self._resolve_path(config.input_file, base_path)
        input_payload = json.loads(input_path.read_text(encoding="utf-8"))

        results: list[ExperimentRunResult] = []
        log_path: Path | None = None
        for template_identifier in config.templates:
            category, template_name = self._split_template_identifier(template_identifier)
            run_result = ExperimentRunResult(
                experiment_name=config.experiment_name,
                template_name=template_identifier,
                input_file=str(input_path),
                validation_status="not_requested",
            )

            try:
                response = self.prompt_engine.run(
                    PromptRequest(
                        category=category,
                        template_name=template_name,
                        input_payload=input_payload,
                        require_json_output=False,
                    )
                )
                run_result.raw_output = response.raw_output
                run_result.model = response.model
                run_result.template_path = response.template_path
                (
                    run_result.validation_status,
                    run_result.validation_error,
                ) = self._validate_output(
                    raw_output=response.raw_output,
                    expects_json=config.expects_json,
                    required_keys=config.required_keys,
                )
            except Exception as exc:  # pragma: no cover - defensive catch
                self.logger.exception(
                    "Experiment run failed for template '%s'.", template_identifier
                )
                run_result.run_status = "failed"
                run_result.run_error = str(exc)
                if config.expects_json:
                    run_result.validation_status = "skipped"
                    run_result.validation_error = "Validation skipped because prompt execution failed."

            log_path = self.evaluator.save_experiment_result(run_result)
            results.append(run_result)

        self._print_summary(config.experiment_name, results, log_path)
        return results

    def _validate_output(
        self,
        raw_output: str,
        expects_json: bool,
        required_keys: list[str],
    ) -> tuple[str, str | None]:
        """Validate a prompt output according to the experiment config."""

        if not expects_json:
            return "not_requested", None

        try:
            parsed_output = validate_json_output(raw_output)
            if required_keys:
                validate_required_keys(parsed_output, required_keys)
        except ValidationError as exc:
            return "failed", str(exc)

        return "passed", None

    def _print_summary(
        self,
        experiment_name: str,
        results: list[ExperimentRunResult],
        log_path: Path | None,
    ) -> None:
        """Print a concise console summary for an experiment run."""

        passed = sum(result.validation_status == "passed" for result in results)
        failed = sum(result.validation_status == "failed" for result in results)
        skipped = sum(result.run_status == "failed" for result in results)

        print(f"Experiment: {experiment_name}")
        print(f"Templates run: {len(results)}")
        print(f"Validation passed: {passed}")
        print(f"Validation failed: {failed}")
        print(f"Run failures: {skipped}")
        if log_path:
            print(f"Experiment log saved to: {log_path}")

    def _resolve_path(self, path_value: str, base_dir: Path) -> Path:
        """Resolve a config-relative or absolute path."""

        path = Path(path_value)
        if path.is_absolute():
            return path
        return (base_dir / path).resolve()

    def _split_template_identifier(self, template_identifier: str) -> tuple[str, str]:
        """Split a category/template identifier into its parts."""

        if "/" not in template_identifier:
            raise ValueError(
                "Template identifiers must use the format 'category/template_name'."
            )
        return tuple(template_identifier.split("/", maxsplit=1))  # type: ignore[return-value]
