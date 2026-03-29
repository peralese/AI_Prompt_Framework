"""Example prompt experiment workflow."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.experiment_runner import ExperimentRunner


def main() -> None:
    example_dir = Path(__file__).resolve().parent
    config_path = example_dir / "data" / "sample_experiment_config.json"

    runner = ExperimentRunner()
    execution = runner.execute_from_config(config_path)
    print("Example run complete.")
    print(f"Runs executed: {len(execution.results)}")
    if execution.readable_report_path:
        print(f"Readable report: {execution.readable_report_path}")


if __name__ == "__main__":
    main()
