import json
from pathlib import Path

from app.evaluator import Evaluator
from app.experiment_runner import ExperimentRunner
from app.models import ExperimentConfig, PromptResponse


class StubPromptEngine:
    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, str, dict]] = []

    def run(self, request) -> PromptResponse:
        template_identifier = f"{request.category}/{request.template_name}"
        self.calls.append(
            (request.category, request.template_name, request.input_payload)
        )
        return PromptResponse(
            template_path=f"/tmp/{request.template_name}.txt",
            rendered_prompt="rendered prompt",
            raw_output=self.responses[template_identifier],
            parsed_output=None,
            model="stub-model",
        )


def test_load_config_reads_experiment_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.json"
    config_path.write_text(
        json.dumps(
            {
                "experiment_name": "summary_comparison",
                "templates": ["summarization/executive_summary"],
                "input_file": "input.json",
                "expects_json": False,
                "required_keys": [],
            }
        ),
        encoding="utf-8",
    )

    runner = ExperimentRunner(
        prompt_engine=StubPromptEngine({}),
        evaluator=Evaluator(experiment_log_dir=tmp_path / "logs"),
    )

    config, resolved_path = runner.load_config(config_path)

    assert config == ExperimentConfig(
        experiment_name="summary_comparison",
        templates=["summarization/executive_summary"],
        input_file="input.json",
        expects_json=False,
        required_keys=[],
    )
    assert resolved_path == config_path.resolve()


def test_load_config_reads_dataset_experiment_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.json"
    config_path.write_text(
        json.dumps(
            {
                "experiment_name": "summary_dataset_comparison",
                "templates": ["summarization/executive_summary"],
                "dataset_file": "dataset.json",
                "expects_json": False,
                "required_keys": [],
            }
        ),
        encoding="utf-8",
    )

    runner = ExperimentRunner(
        prompt_engine=StubPromptEngine({}),
        evaluator=Evaluator(experiment_log_dir=tmp_path / "logs"),
    )

    config, resolved_path = runner.load_config(config_path)

    assert config == ExperimentConfig(
        experiment_name="summary_dataset_comparison",
        templates=["summarization/executive_summary"],
        dataset_file="dataset.json",
        expects_json=False,
        required_keys=[],
    )
    assert resolved_path == config_path.resolve()


def test_run_experiment_executes_multiple_templates(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_payload = {"status": "In delivery"}
    input_path.write_text(json.dumps(input_payload), encoding="utf-8")

    runner = ExperimentRunner(
        prompt_engine=StubPromptEngine(
            {
                "summarization/executive_summary": "Summary A",
                "summarization/executive_summary_v2": "Summary B",
            }
        ),
        evaluator=Evaluator(experiment_log_dir=tmp_path / "logs"),
    )

    results = runner.run_experiment(
        ExperimentConfig(
            experiment_name="summary_prompt_comparison",
            templates=[
                "summarization/executive_summary",
                "summarization/executive_summary_v2",
            ],
            input_file=str(input_path),
        ),
        base_dir=tmp_path,
    )

    assert len(results) == 2
    assert [result.template_name for result in results] == [
        "summarization/executive_summary",
        "summarization/executive_summary_v2",
    ]
    assert all(result.raw_output for result in results)
    assert all(result.validation_status == "not_requested" for result in results)


def test_run_experiment_executes_dataset_cases(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_name": "summary_dataset",
                "category": "summarization",
                "cases": [
                    {
                        "case_id": "case_1",
                        "description": "First summary case",
                        "input_payload": {"status": "In delivery"},
                    },
                    {
                        "case_id": "case_2",
                        "description": "Second summary case",
                        "input_payload": {"status": "Blocked"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = ExperimentRunner(
        prompt_engine=StubPromptEngine(
            {
                "summarization/executive_summary": "Summary output",
                "summarization/executive_summary_v2": "Summary output v2",
            }
        ),
        evaluator=Evaluator(experiment_log_dir=tmp_path / "logs"),
    )

    results = runner.run_experiment(
        ExperimentConfig(
            experiment_name="summary_dataset_comparison",
            templates=[
                "summarization/executive_summary",
                "summarization/executive_summary_v2",
            ],
            dataset_file=str(dataset_path),
        ),
        base_dir=tmp_path,
    )

    assert len(results) == 4
    assert {result.case_id for result in results} == {"case_1", "case_2"}
    assert {result.dataset_name for result in results} == {"summary_dataset"}
    assert all(result.validation_status == "not_requested" for result in results)


def test_run_experiment_records_successful_json_validation(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps({"items": ["redis"]}), encoding="utf-8")

    log_dir = tmp_path / "logs"
    runner = ExperimentRunner(
        prompt_engine=StubPromptEngine(
            {
                "classification/software_classifier": '{"items": [{"name": "Redis"}]}',
            }
        ),
        evaluator=Evaluator(experiment_log_dir=log_dir),
    )

    results = runner.run_experiment(
        ExperimentConfig(
            experiment_name="classification_comparison",
            templates=["classification/software_classifier"],
            input_file=str(input_path),
            expects_json=True,
            required_keys=["items"],
        ),
        base_dir=tmp_path,
    )

    assert results[0].validation_status == "passed"
    assert results[0].validation_error is None

    log_path = log_dir / "classification_comparison.jsonl"
    assert log_path.exists()
    logged_result = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert logged_result["validation_status"] == "passed"


def test_run_experiment_continues_after_validation_failure(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps({"text": "messy notes"}), encoding="utf-8")

    runner = ExperimentRunner(
        prompt_engine=StubPromptEngine(
            {
                "extraction/structured_extraction": "not-json",
                "extraction/structured_extraction_v2": '{"owner": "Alex", "deadline": null}',
            }
        ),
        evaluator=Evaluator(experiment_log_dir=tmp_path / "logs"),
    )

    results = runner.run_experiment(
        ExperimentConfig(
            experiment_name="extraction_comparison",
            templates=[
                "extraction/structured_extraction",
                "extraction/structured_extraction_v2",
            ],
            input_file=str(input_path),
            expects_json=True,
            required_keys=["owner", "deadline"],
        ),
        base_dir=tmp_path,
    )

    assert [result.validation_status for result in results] == ["failed", "passed"]
    assert results[0].validation_error is not None
    assert results[1].validation_error is None
