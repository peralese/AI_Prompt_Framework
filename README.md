# AI Prompt Framework

AI Prompt Framework is a reusable, plain-Python prompt engineering toolkit for local AI development. The project is intentionally general-purpose: it is designed to support many prompt-driven tasks without becoming primarily about one project, workflow, or domain.

The framework keeps the architecture explicit and lightweight:

- prompt templates live on disk
- structured input is converted into deterministic prompt context
- the prompt engine handles template injection and model calls
- validators handle JSON parsing and required-key checks
- evaluation and experiment logs capture what was run and what happened

Examples are demonstrations, not the definition of the framework. The included prompt categories show how the toolkit can be used for classification, summarization, extraction, and decisioning, but the core code should remain reusable across prompt categories. Experimentation should stay category-neutral where possible.

## Current Architecture

```text
app/
  __init__.py
  config.py
  context_builder.py
  evaluator.py
  experiment_runner.py
  llm_client.py
  logger.py
  models.py
  prompt_engine.py
  template_loader.py
  validators.py
prompts/
  classification/
  decisioning/
  extraction/
  summarization/
datasets/
examples/
  data/
  run_classification_example.py
  run_decision_example.py
  run_experiment_example.py
  run_extraction_example.py
  run_summary_example.py
evaluation_logs/
experiment_logs/
tests/
README.md
requirements.txt
```

## Phase 1 Capabilities

Phase 1 established the reusable prompt engine foundation:

- template loading by category and name
- deterministic context building from dictionaries and lists
- OpenAI integration through an isolated provider wrapper
- JSON output validation and required-key checks
- centralized console logging
- JSONL-based evaluation logging
- runnable examples across multiple prompt categories
- pytest coverage for core utility modules

## Phase 2 Roadmap

- Phase 2A: Completed. Generic prompt experiment harness for comparing prompt versions against the same structured input
- Phase 2B: Completed. Reusable evaluation datasets across prompt categories
- Phase 2C: Evaluation rubric and scoring model
- Phase 2D: Human-readable experiment summaries and findings
- Later ideas:
  - multiple LLM providers behind a shared interface
  - richer schema validation and typed extraction flows
  - prompt versioning strategy and naming conventions
  - multi-step prompt pipelines

## Phase 2A: Prompt Experiment Harness

Phase 2A is complete. It adds a generic comparison harness that runs multiple templates against the same input payload. This makes it easier to test prompt variations, compare prompt designs, and document what works without tying the framework to a single task type.

The experiment harness is category-neutral:

- it loads a simple JSON config
- it reads one structured input file
- it runs each template listed in the config against that same input
- it optionally validates JSON output and required keys
- it records one JSONL result per template run under `experiment_logs/`
- it continues through validation failures so one bad prompt variant does not stop the experiment

This supports Week 9 style goals around testing variations, comparing prompt designs, and keeping a written record of findings.

Completed deliverables in this phase:

- `ExperimentRunner` for loading configs and running template comparisons
- reusable experiment config and result models
- JSONL experiment logging under `experiment_logs/`
- optional generic JSON validation with non-fatal failures
- an example experiment config and runner script
- test coverage for config loading, multi-template execution, and validation behavior

## Phase 2B: Reusable Evaluation Datasets

Phase 2B is complete. It extends the experiment harness so experiments can run reusable multi-case datasets instead of only a single input file. This keeps experimentation generic while making it easier to compare prompt variants across a broader set of structured inputs.

The dataset layer is still category-neutral:

- datasets are plain JSON files under `datasets/`
- each dataset has a `dataset_name` and a list of reusable `cases`
- each case has a `case_id` plus an `input_payload`
- experiments can now point to either `input_file` or `dataset_file`
- the experiment runner executes every template against every dataset case
- experiment logs now capture dataset and case identifiers for later scoring and reporting

Completed deliverables in this phase:

- reusable dataset models and a dataset loader
- support for `dataset_file` in experiment configs
- multi-case experiment execution across templates
- a generic summarization evaluation dataset
- pytest coverage for dataset loading and dataset-based experiment runs

## Example Prompt Categories

The included examples demonstrate common prompt patterns:

- `classification`: categorize a list of tools, technologies, or other items into structured labels
- `summarization`: convert structured notes into concise executive-facing summaries
- `extraction`: pull structured fields from messy source text while leaving unknown values as `null`
- `decisioning`: recommend a next step from options, constraints, and tradeoffs

These are examples, not limits. You can add your own templates under `prompts/` and create new flows without changing the core engine.

## Experiment Config Format

Experiments use a small JSON config file:

```json
{
  "experiment_name": "summary_prompt_comparison",
  "templates": [
    "summarization/executive_summary",
    "summarization/executive_summary_v2"
  ],
  "dataset_file": "../../datasets/summary_evaluation_dataset.json",
  "expects_json": false,
  "required_keys": []
}
```

Fields:

- `experiment_name`: required
- `templates`: required list of `category/template_name` identifiers
- `input_file`: required path to a structured JSON payload
- `dataset_file`: optional path to a reusable dataset JSON file
- `expects_json`: optional boolean for JSON validation
- `required_keys`: optional list of keys that must exist when JSON validation is enabled

An experiment should provide either `input_file` for a single-case run or `dataset_file` for a reusable multi-case run.

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

File naming is enough for prompt version comparison in this phase. For example:

- `summarization/executive_summary`
- `summarization/executive_summary_v2`
- `extraction/structured_extraction`
- `extraction/structured_extraction_v2`

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

3. Create an environment file if needed and set your API key.

```bash
cp .env.example .env
```

## Environment Variables

- `OPENAI_API_KEY`: required for OpenAI requests
- `OPENAI_MODEL`: optional, defaults to `gpt-4.1-mini`
- `LOG_LEVEL`: optional, defaults to `INFO`

## Running Examples

Run the examples from the repository root:

```bash
python3 examples/run_classification_example.py
python3 examples/run_summary_example.py
python3 examples/run_extraction_example.py
python3 examples/run_decision_example.py
python3 examples/run_experiment_example.py
```

The experiment example uses [examples/data/sample_experiment_config.json](/home/peralese/Projects/AI_Prompt_Framework/examples/data/sample_experiment_config.json) and [datasets/summary_evaluation_dataset.json](/home/peralese/Projects/AI_Prompt_Framework/datasets/summary_evaluation_dataset.json) to compare two summarization templates across a reusable multi-case dataset.

## How Experiments Work

1. Create or reuse one structured input JSON file or a reusable dataset file.
2. List one or more template identifiers in an experiment config.
3. Run the experiment example or call `ExperimentRunner` directly.
4. Review console output for the high-level summary.
5. Review `experiment_logs/<experiment_name>.jsonl` for per-template results.

Each experiment record captures:

- timestamp
- experiment name
- template name
- input file
- dataset name, when applicable
- case id, when applicable
- raw output
- validation status
- validation error, if any
- run status and run error, if a prompt execution failed

## Evaluation And Experiment Logs

- `evaluation_logs/` stores general prompt run records from the example scripts
- `experiment_logs/` stores one JSONL file per experiment, with one record per template run

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
5. Add an example script, experiment config, or test if you want a reusable workflow

To compare prompt variants:

1. Add a second template file such as `_v2`
2. Create an experiment config listing both variants
3. Run the experiment harness
4. Review the JSONL experiment log and compare outputs

To reuse evaluation inputs across experiments:

1. Create a dataset file under `datasets/`
2. Add multiple named cases with structured payloads
3. Point an experiment config at `dataset_file`
4. Reuse that dataset across prompt versions and categories where appropriate

This keeps the framework general-purpose while making prompt experimentation explicit and repeatable.
