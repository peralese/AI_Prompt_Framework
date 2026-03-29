# AI Prompt Framework

AI Prompt Framework is a reusable, plain-Python prompt engineering toolkit for local AI development. The project is intentionally general-purpose: it is designed to support many prompt-driven tasks without becoming primarily about one project, workflow, or domain.

The framework now supports both prompt experimentation and live prompt testing:

- prompt templates live on disk
- structured input is converted into deterministic prompt context
- the prompt engine handles template injection and model calls
- validators handle JSON parsing and required-key checks
- datasets and rubrics support repeatable comparisons
- experiment logs and reports capture what was run and what happened
- a root-level CLI supports real input files from the project root

Examples are demonstrations, not the definition of the framework. The included prompt categories show how the toolkit can be used for classification, summarization, extraction, and decisioning, but the core code remains reusable across prompt categories.

The framework is evolving from a prompt lab into a usable prompt testing tool. Experimentation remains important, but the primary interface for live use is now the root-level CLI.

## Current Architecture

```text
app/
  __init__.py
  config.py
  context_builder.py
  dataset_loader.py
  evaluator.py
  experiment_runner.py
  llm_client.py
  logger.py
  models.py
  prompt_engine.py
  report_generator.py
  rubric_loader.py
  scorer.py
  template_loader.py
  validators.py
configs/
data/
  live/
  test/
datasets/
examples/
  data/
prompts/
  classification/
  decisioning/
  extraction/
  summarization/
rubrics/
evaluation_logs/
experiment_logs/
experiment_reports/
run_experiment.py
tests/
README.md
requirements.txt
```

## Operational Usage

The primary way to run the tool is from the project root:

```bash
python3 run_experiment.py --config configs/live_summary_test.json
```

This supports real input files without relying on `examples/run_experiment_example.py`.

Supported usage patterns:

Config-driven run:

```bash
python3 run_experiment.py --config configs/live_summary_test.json
```

Direct one-off run with a single input file:

```bash
python3 run_experiment.py \
  --templates summarization/executive_summary summarization/executive_summary_v2 \
  --input-file data/live/sample_summary_live.json \
  --experiment-name live_summary_test
```

Direct dataset run:

```bash
python3 run_experiment.py \
  --templates summarization/executive_summary summarization/executive_summary_v2 \
  --dataset-file data/test/summary_dataset.json \
  --experiment-name summary_dataset_comparison
```

Optional CLI flags:

- `--rubric-file rubrics/summary_quality_rubric.json`
- `--expects-json`
- `--required-keys key1 key2`
- `--show-output`

When `--show-output` is enabled, the CLI prints the readable case-by-case comparison output directly to the terminal.

## Live Testing And Experimentation

Operational / live testing mode:

- `run_experiment.py` is the primary entry point
- `configs/` can store reusable run configs
- `data/live/` is for real user-supplied input files
- `data/test/` is for local test inputs
- output artifacts are written to `experiment_logs/` and `experiment_reports/`

Experimentation / development mode:

- `examples/` contains optional demos
- `datasets/` contains reusable evaluation datasets
- `rubrics/` contains reusable scoring rubrics
- this mode is useful for template iteration, prompt tuning, and regression-style comparisons

## Phase Roadmap

- Phase 1: Completed. Core prompt engine, templates, context builder, validation, and evaluation logging
- Phase 2A: Completed. Generic prompt experiment harness for comparing prompt versions
- Phase 2B: Completed. Reusable evaluation datasets across prompt categories
- Phase 2C: Completed. Evaluation rubric and scoring model
- Phase 2D: Completed. Human-readable experiment summaries and readable comparison reports
- Later ideas:
  - multiple LLM providers behind a shared interface
  - richer schema validation and typed extraction flows
  - prompt versioning strategy and naming conventions
  - multi-step prompt pipelines

## Experiment Config Format

Experiments use a small generic JSON config file.

Single-file mode:

```json
{
  "experiment_name": "live_summary_test",
  "templates": [
    "summarization/executive_summary",
    "summarization/executive_summary_v2"
  ],
  "input_file": "data/live/sample_summary_live.json",
  "rubric_file": "rubrics/summary_quality_rubric.json",
  "expects_json": false,
  "required_keys": []
}
```

Dataset mode:

```json
{
  "experiment_name": "summary_prompt_comparison",
  "templates": [
    "summarization/executive_summary",
    "summarization/executive_summary_v2"
  ],
  "dataset_file": "data/test/summary_dataset.json",
  "rubric_file": "rubrics/summary_quality_rubric.json",
  "expects_json": false,
  "required_keys": []
}
```

Fields:

- `experiment_name`: required
- `templates`: required list of `category/template_name` identifiers
- `input_file`: optional path to a single structured JSON input file
- `dataset_file`: optional path to a reusable dataset JSON file
- `rubric_file`: optional path to a reusable rubric JSON file
- `expects_json`: optional boolean for JSON validation
- `required_keys`: optional list of keys that must exist when JSON validation is enabled

An experiment should provide either `input_file` or `dataset_file`. A rubric is optional and can be layered onto either mode.

## Dataset Format

Reusable datasets use a simple JSON structure:

```json
{
  "dataset_name": "summary_evaluation_dataset",
  "category": "summarization",
  "cases": [
    {
      "case_id": "summary_case_1",
      "description": "Delivery status update with risks and next actions",
      "input_payload": {
        "project_name": "Customer Insights Dashboard",
        "status": "In delivery"
      }
    }
  ]
}
```

Fields:

- `dataset_name`: required
- `category`: optional descriptive label
- `cases`: required list of reusable prompt input cases
- `case_id`: required per case
- `input_payload`: required per case
- `description`: optional per case
- `notes`: optional per case

## Rubric Format

Reusable rubrics use a simple JSON structure:

```json
{
  "rubric_name": "summary_quality_rubric",
  "category": "summarization",
  "criteria": [
    {
      "criterion_id": "non_empty_output",
      "description": "The output should not be empty.",
      "rule_type": "non_empty_output",
      "weight": 1.0
    }
  ]
}
```

Fields:

- `rubric_name`: required
- `category`: optional descriptive label
- `criteria`: required list of weighted scoring criteria
- `criterion_id`: required per criterion
- `description`: required per criterion
- `rule_type`: required per criterion
- `weight`: optional per criterion, defaults to `1.0`
- `config`: optional rule-specific settings

Current generic rule types:

- `non_empty_output`
- `validation_passed`
- `output_length_between`
- `contains_any_input_values`
- `contains_all_strings`
- `json_keys_present`

## Console Output And Saved Artifacts

When you run the root CLI, the console output shows:

- experiment name
- number of cases
- whether the run is single-case
- templates being compared
- validation and scoring summary
- where JSONL logs were written
- where markdown reports were written

Generated artifacts:

- `experiment_logs/<experiment_name>.jsonl`
- `experiment_reports/<experiment_name>.md`
- `experiment_reports/<experiment_name>_readable.md`

The readable comparison report is optimized for humans. It groups results by case and shows:

- the input payload
- each template output under the same case
- validation status
- rubric score when available
- notes when available

## Real-Usage Sample Config

A root-level live testing config is included at [configs/live_summary_test.json](/home/peralese/Projects/AI_Prompt_Framework/configs/live_summary_test.json). It uses [data/live/sample_summary_live.json](/home/peralese/Projects/AI_Prompt_Framework/data/live/sample_summary_live.json) and can be run with:

```bash
python3 run_experiment.py --config configs/live_summary_test.json
```

## Running Examples

Examples remain available as optional demos:

```bash
python3 examples/run_classification_example.py
python3 examples/run_summary_example.py
python3 examples/run_extraction_example.py
python3 examples/run_decision_example.py
python3 examples/run_experiment_example.py
```

The experiment demo uses [examples/data/sample_experiment_config.json](/home/peralese/Projects/AI_Prompt_Framework/examples/data/sample_experiment_config.json), [datasets/summary_evaluation_dataset.json](/home/peralese/Projects/AI_Prompt_Framework/datasets/summary_evaluation_dataset.json), and [rubrics/summary_quality_rubric.json](/home/peralese/Projects/AI_Prompt_Framework/rubrics/summary_quality_rubric.json).

## Example Prompt Categories

The included prompts and examples demonstrate common patterns:

- `classification`
- `summarization`
- `extraction`
- `decisioning`

These are examples, not limits.

## Setup

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create an environment file and set your API key.

```bash
cp .env.example .env
```

## Environment Variables

- `OPENAI_API_KEY`: required for OpenAI requests
- `OPENAI_MODEL`: optional, defaults to `gpt-4.1-mini`
- `LOG_LEVEL`: optional, defaults to `INFO`

## Running Tests

```bash
pytest
```

## Extending The Toolkit

To add a new use case:

1. Create a new prompt template under a category in `prompts/`
2. Prepare a structured input payload
3. Build a `PromptRequest` with the template name and input data
4. Enable JSON validation if the prompt is expected to return structured output
5. Add a config, dataset, rubric, or example if you want a reusable workflow

To compare prompt variants:

1. Add a second template file such as `_v2`
2. Create a config listing both variants
3. Run `python3 run_experiment.py --config ...`
4. Review the JSONL log and markdown reports

This keeps the framework general-purpose while making prompt experimentation and live testing both first-class workflows.
