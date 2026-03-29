from __future__ import annotations

from pathlib import Path

import pytest

import run_experiment
from app.models import ExperimentConfig, ExperimentExecution, ExperimentReport


class FakeRunner:
    last_config_path: str | None = None
    last_config: ExperimentConfig | None = None
    last_base_dir: Path | None = None

    def execute_from_config(self, config_path: str) -> ExperimentExecution:
        type(self).last_config_path = config_path
        return ExperimentExecution(
            experiment_name="config_run",
            template_names=["summarization/executive_summary"],
            case_count=2,
            results=[],
            log_path="experiment_logs/config_run.jsonl",
            report_path="experiment_reports/config_run.md",
            readable_report_path="experiment_reports/config_run_readable.md",
            report=ExperimentReport(
                experiment_name="config_run",
                total_runs=0,
                total_templates=1,
                total_cases=2,
                markdown="# Config Report",
                readable_markdown="# Readable Config Report",
            ),
        )

    def execute_experiment(
        self, config: ExperimentConfig, base_dir: Path | None = None
    ) -> ExperimentExecution:
        type(self).last_config = config
        type(self).last_base_dir = base_dir
        return ExperimentExecution(
            experiment_name=config.experiment_name,
            template_names=config.templates,
            case_count=1 if config.input_file else 2,
            results=[],
            log_path=f"experiment_logs/{config.experiment_name}.jsonl",
            report_path=f"experiment_reports/{config.experiment_name}.md",
            readable_report_path=f"experiment_reports/{config.experiment_name}_readable.md",
            report=ExperimentReport(
                experiment_name=config.experiment_name,
                total_runs=0,
                total_templates=len(config.templates),
                total_cases=1 if config.input_file else 2,
                markdown="# Direct Report",
                readable_markdown="# Readable Direct Report",
            ),
        )


def test_cli_runs_with_config_mode(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = run_experiment.main(
        ["--config", "examples/data/sample_experiment_config.json"],
        runner_cls=FakeRunner,
    )

    assert exit_code == 0
    assert FakeRunner.last_config_path == "examples/data/sample_experiment_config.json"
    assert "Readable Direct Report" not in capsys.readouterr().out


def test_cli_runs_with_direct_input_file_mode() -> None:
    exit_code = run_experiment.main(
        [
            "--templates",
            "summarization/executive_summary",
            "summarization/executive_summary_v2",
            "--input-file",
            "data/live/sample_summary_live.json",
            "--experiment-name",
            "live_summary_test",
            "--rubric-file",
            "rubrics/summary_quality_rubric.json",
        ],
        runner_cls=FakeRunner,
    )

    assert exit_code == 0
    assert FakeRunner.last_config is not None
    assert FakeRunner.last_config.experiment_name == "live_summary_test"
    assert FakeRunner.last_config.input_file == "data/live/sample_summary_live.json"
    assert FakeRunner.last_config.templates == [
        "summarization/executive_summary",
        "summarization/executive_summary_v2",
    ]


def test_cli_supports_show_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = run_experiment.main(
        [
            "--templates",
            "summarization/executive_summary",
            "--input-file",
            "data/live/sample_summary_live.json",
            "--experiment-name",
            "live_summary_test",
            "--show-output",
        ],
        runner_cls=FakeRunner,
    )

    assert exit_code == 0
    assert "# Readable Direct Report" in capsys.readouterr().out


def test_cli_direct_mode_supports_dataset_file() -> None:
    exit_code = run_experiment.main(
        [
            "--templates",
            "summarization/executive_summary",
            "--dataset-file",
            "data/test/summary_dataset.json",
            "--experiment-name",
            "dataset_run",
        ],
        runner_cls=FakeRunner,
    )

    assert exit_code == 0
    assert FakeRunner.last_config is not None
    assert FakeRunner.last_config.dataset_file == "data/test/summary_dataset.json"
    assert FakeRunner.last_config.input_file is None


def test_cli_rejects_invalid_direct_mode_arguments() -> None:
    with pytest.raises(SystemExit):
        run_experiment.main(
            [
                "--templates",
                "summarization/executive_summary",
                "--experiment-name",
                "invalid_run",
            ],
            runner_cls=FakeRunner,
        )
