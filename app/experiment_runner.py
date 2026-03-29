"""Generic prompt experiment runner for comparing template variants."""

from __future__ import annotations

import json
from pathlib import Path

from .dataset_loader import DatasetLoader
from .evaluator import Evaluator
from .logger import get_logger
from .models import DatasetCase, ExperimentConfig, ExperimentRunResult, PromptRequest
from .prompt_engine import PromptEngine
from .report_generator import ExperimentReportGenerator
from .rubric_loader import RubricLoader
from .scorer import ExperimentScorer, ScoringError
from .validators import ValidationError, validate_json_output, validate_required_keys


class ExperimentRunner:
    """Run a reusable prompt comparison experiment across multiple templates."""

    def __init__(
        self,
        prompt_engine: PromptEngine | None = None,
        evaluator: Evaluator | None = None,
        dataset_loader: DatasetLoader | None = None,
        rubric_loader: RubricLoader | None = None,
        scorer: ExperimentScorer | None = None,
        report_generator: ExperimentReportGenerator | None = None,
    ) -> None:
        self.prompt_engine = prompt_engine or PromptEngine()
        self.evaluator = evaluator or Evaluator()
        self.dataset_loader = dataset_loader or DatasetLoader()
        self.rubric_loader = rubric_loader or RubricLoader()
        self.scorer = scorer or ExperimentScorer()
        self.report_generator = report_generator or ExperimentReportGenerator()
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
        dataset_name = None
        rubric = None
        if config.rubric_file:
            rubric_path = self._resolve_path(config.rubric_file, base_path)
            rubric, _ = self.rubric_loader.load(rubric_path)
        if config.dataset_file:
            dataset_path = self._resolve_path(config.dataset_file, base_path)
            dataset, resolved_dataset_path = self.dataset_loader.load(dataset_path)
            dataset_name = dataset.dataset_name
            cases = dataset.cases
            input_reference = str(resolved_dataset_path)
        else:
            if not config.input_file:
                raise ValueError(
                    "Experiment config must include either 'input_file' or 'dataset_file'."
                )
            input_path = self._resolve_path(config.input_file, base_path)
            input_payload = json.loads(input_path.read_text(encoding="utf-8"))
            cases = [DatasetCase(case_id="input_1", input_payload=input_payload)]
            input_reference = str(input_path)

        results: list[ExperimentRunResult] = []
        log_path: Path | None = None
        report_path: Path | None = None
        readable_report_path: Path | None = None
        for case in cases:
            for template_identifier in config.templates:
                category, template_name = self._split_template_identifier(
                    template_identifier
                )
                run_result = ExperimentRunResult(
                    experiment_name=config.experiment_name,
                    template_name=template_identifier,
                    input_file=input_reference,
                    dataset_name=dataset_name,
                    case_id=case.case_id,
                    case_description=case.description,
                    input_payload=case.input_payload,
                    notes=case.notes,
                    rubric_name=rubric.rubric_name if rubric else None,
                    validation_status="not_requested",
                )

                try:
                    response = self.prompt_engine.run(
                        PromptRequest(
                            category=category,
                            template_name=template_name,
                            input_payload=case.input_payload,
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
                    if rubric:
                        (
                            run_result.scoring_status,
                            run_result.scoring_error,
                            run_result.rubric_score,
                            run_result.rubric_max_score,
                            run_result.rubric_breakdown,
                        ) = self._score_output(
                            run_result=run_result,
                            input_payload=case.input_payload,
                            rubric=rubric,
                        )
                except Exception as exc:  # pragma: no cover - defensive catch
                    self.logger.exception(
                        "Experiment run failed for template '%s'.", template_identifier
                    )
                    run_result.run_status = "failed"
                    run_result.run_error = str(exc)
                    if config.expects_json:
                        run_result.validation_status = "skipped"
                        run_result.validation_error = (
                            "Validation skipped because prompt execution failed."
                        )
                    if rubric:
                        run_result.scoring_status = "skipped"
                        run_result.scoring_error = (
                            "Scoring skipped because prompt execution failed."
                        )

                log_path = self.evaluator.save_experiment_result(run_result)
                results.append(run_result)

        report = self.report_generator.generate_report(config.experiment_name, results)
        report_path = self.evaluator.save_experiment_report(report)
        readable_report_path = self.evaluator.save_readable_experiment_report(report)
        self._print_summary(
            config.experiment_name,
            results,
            log_path,
            report_path,
            readable_report_path,
            len(cases),
            rubric_enabled=rubric is not None,
        )
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

    def _score_output(
        self,
        run_result: ExperimentRunResult,
        input_payload: dict,
        rubric,
    ) -> tuple[str, str | None, float | None, float | None, list[dict]]:
        """Score a prompt output according to the selected rubric."""

        try:
            score, max_score, breakdown = self.scorer.score_run(
                run_result=run_result,
                input_payload=input_payload,
                rubric=rubric,
            )
        except ScoringError as exc:
            return "failed", str(exc), None, None, []

        return "scored", None, score, max_score, breakdown

    def _print_summary(
        self,
        experiment_name: str,
        results: list[ExperimentRunResult],
        log_path: Path | None,
        report_path: Path | None,
        readable_report_path: Path | None,
        case_count: int,
        rubric_enabled: bool,
    ) -> None:
        """Print a concise console summary for an experiment run."""

        passed = sum(result.validation_status == "passed" for result in results)
        failed = sum(result.validation_status == "failed" for result in results)
        skipped = sum(result.run_status == "failed" for result in results)
        scored = sum(result.scoring_status == "scored" for result in results)
        average_score = None
        score_values = [
            (result.rubric_score or 0.0, result.rubric_max_score or 0.0)
            for result in results
            if result.scoring_status == "scored"
            and result.rubric_score is not None
            and result.rubric_max_score
        ]
        if score_values:
            average_score = sum(score / max_score for score, max_score in score_values) / len(
                score_values
            )

        print(f"Experiment: {experiment_name}")
        print(f"Cases run: {case_count}")
        print(f"Templates run: {len(results)}")
        print(f"Validation passed: {passed}")
        print(f"Validation failed: {failed}")
        print(f"Run failures: {skipped}")
        if rubric_enabled:
            print(f"Scored runs: {scored}")
            if average_score is not None:
                print(f"Average rubric score: {average_score:.2%}")
        if log_path:
            print(f"Experiment log saved to: {log_path}")
        if report_path:
            print(f"Experiment report saved to: {report_path}")
        if readable_report_path:
            print(f"Readable comparison report saved to: {readable_report_path}")

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
