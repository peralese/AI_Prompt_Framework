"""Example decisioning workflow."""

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
    data_path = example_dir / "data" / "sample_decision.json"
    input_payload = json.loads(data_path.read_text(encoding="utf-8"))

    engine = PromptEngine()
    request = PromptRequest(
        category="decisioning",
        template_name="recommend_next_step",
        input_payload=input_payload,
        require_json_output=True,
        required_keys=["recommended_option", "justification", "risks", "assumptions"],
    )
    response = engine.run(request)

    print("Decision Recommendation")
    print(json.dumps(response.parsed_output, indent=2))

    evaluator = Evaluator()
    log_path = evaluator.save_result(
        prompt_name="decision_example",
        input_payload=input_payload,
        output_text=response.raw_output,
        notes="General-purpose decisioning example.",
    )
    print(f"Evaluation log saved to: {log_path}")


if __name__ == "__main__":
    main()
