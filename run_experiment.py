"""Root-level CLI for running prompt experiments and live prompt comparisons."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from app.experiment_runner import ExperimentRunner
from app.models import ExperimentConfig


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Run prompt experiments from the project root."
    )
    parser.add_argument("--config", help="Path to an experiment config JSON file.")
    parser.add_argument(
        "--templates",
        nargs="+",
        help="One or more template identifiers such as summarization/executive_summary.",
    )
    parser.add_argument(
        "--input-file",
        help="Path to a single input JSON file for a one-off run.",
    )
    parser.add_argument(
        "--dataset-file",
        help="Path to a dataset JSON file for a multi-case run.",
    )
    parser.add_argument(
        "--experiment-name",
        help="Experiment name to use for direct runs.",
    )
    parser.add_argument(
        "--rubric-file",
        help="Optional rubric JSON file.",
    )
    parser.add_argument(
        "--expects-json",
        action="store_true",
        help="Validate outputs as JSON.",
    )
    parser.add_argument(
        "--required-keys",
        nargs="*",
        default=[],
        help="Required keys to validate when --expects-json is enabled.",
    )
    parser.add_argument(
        "--show-output",
        action="store_true",
        help="Print the readable comparison output to the terminal.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    runner_cls: type[ExperimentRunner] = ExperimentRunner,
) -> int:
    """Run the CLI and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.config:
        if args.templates or args.input_file or args.dataset_file or args.experiment_name:
            parser.error(
                "--config cannot be combined with direct run arguments such as "
                "--templates, --input-file, --dataset-file, or --experiment-name."
            )
        runner = runner_cls()
        execution = runner.execute_from_config(args.config)
    else:
        if not args.templates:
            parser.error("Direct mode requires --templates.")
        if not args.experiment_name:
            parser.error("Direct mode requires --experiment-name.")
        if bool(args.input_file) == bool(args.dataset_file):
            parser.error("Direct mode requires exactly one of --input-file or --dataset-file.")

        config = ExperimentConfig(
            experiment_name=args.experiment_name,
            templates=args.templates,
            input_file=args.input_file,
            dataset_file=args.dataset_file,
            rubric_file=args.rubric_file,
            expects_json=args.expects_json,
            required_keys=args.required_keys,
        )
        runner = runner_cls()
        execution = runner.execute_experiment(config, base_dir=Path.cwd())

    if args.show_output and execution.report is not None:
        print("")
        print(execution.report.readable_markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
