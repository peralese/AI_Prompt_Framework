"""Example structured extraction workflow."""

import json
from pathlib import Path

from prompt_engine.app.evaluator import Evaluator
from prompt_engine.app.models import PromptRequest
from prompt_engine.app.prompt_engine import PromptEngine


def main() -> None:
    example_dir = Path(__file__).resolve().parent
    data_path = example_dir / "data" / "sample_extraction.json"
    input_payload = json.loads(data_path.read_text(encoding="utf-8"))

    engine = PromptEngine()
    request = PromptRequest(
        category="extraction",
        template_name="structured_extraction",
        input_payload=input_payload,
        require_json_output=True,
        required_keys=["owner", "deadline", "status", "risk"],
    )
    response = engine.run(request)

    print("Structured Extraction Result")
    print(json.dumps(response.parsed_output, indent=2))

    evaluator = Evaluator()
    log_path = evaluator.save_result(
        prompt_name="extraction_example",
        input_payload=input_payload,
        output_text=response.raw_output,
        notes="General-purpose extraction example.",
    )
    print(f"Evaluation log saved to: {log_path}")


if __name__ == "__main__":
    main()
