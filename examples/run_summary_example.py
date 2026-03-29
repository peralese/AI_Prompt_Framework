"""Example executive summary workflow."""

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluator import Evaluator
from app.models import PromptRequest
from app.prompt_engine import PromptEngine


def main() -> None:
    example_dir = Path(__file__).resolve().parent
    data_path = example_dir / "data" / "sample_summary.json"
    input_payload = json.loads(data_path.read_text(encoding="utf-8"))

    engine = PromptEngine()
    request = PromptRequest(
        category="summarization",
        template_name="executive_summary",
        input_payload=input_payload,
    )
    response = engine.run(request)
    print("Executive Summary")
    print(response.raw_output)

    evaluator = Evaluator()
    log_path = evaluator.save_result(
        prompt_name="summary_example",
        input_payload=input_payload,
        output_text=response.raw_output,
        notes="General-purpose summarization example.",
    )
    print(f"Evaluation log saved to: {log_path}")


if __name__ == "__main__":
    main()
