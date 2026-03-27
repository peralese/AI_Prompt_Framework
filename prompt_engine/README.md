# Prompt Engineering Toolkit

This project is a reusable, plain-Python Prompt Engineering Toolkit for local AI development. It is intentionally general-purpose: the core engine is designed to support many prompt-driven tasks without locking the project into one domain or workflow.

The toolkit keeps the architecture explicit and lightweight:

- prompt templates live on disk
- structured input is converted into deterministic prompt context
- the prompt engine handles template injection and model calls
- validators handle JSON parsing and key checks
- evaluation logs capture what was run and how it performed

## Current Phase 1 Capabilities

- Reusable prompt engine orchestration
- Template loading by category and name
- Structured context building from dictionaries and lists
- OpenAI integration through an isolated provider wrapper
- JSON output validation and required-key checks
- Centralized console logging
- JSONL-based evaluation logging
- Runnable examples across multiple prompt categories
- Pytest coverage for core utility modules

## Example Categories

The included examples demonstrate four common prompt patterns:

- `classification`: categorize a list of tools, technologies, or other items into structured labels
- `summarization`: convert structured notes into concise executive-facing summaries
- `extraction`: pull structured fields from messy source text while leaving unknown values as `null`
- `decisioning`: recommend a next step from options, constraints, and tradeoffs

These are examples, not limits. You can add your own templates under `prompts/` and create new flows without changing the core engine.

## Folder Structure

```text
prompt_engine/
  app/
    __init__.py
    config.py
    context_builder.py
    evaluator.py
    llm_client.py
    logger.py
    models.py
    prompt_engine.py
    template_loader.py
    validators.py
  prompts/
    classification/
      software_classifier.txt
    decisioning/
      recommend_next_step.txt
    extraction/
      structured_extraction.txt
    summarization/
      executive_summary.txt
  examples/
    data/
      sample_classification.json
      sample_decision.json
      sample_extraction.json
      sample_summary.json
    run_classification_example.py
    run_decision_example.py
    run_extraction_example.py
    run_summary_example.py
  tests/
    test_context_builder.py
    test_prompt_engine.py
    test_template_loader.py
    test_validators.py
  .env.example
  requirements.txt
  README.md
```

## Setup

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r prompt_engine/requirements.txt
```

3. Copy the example environment file and set your API key.

```bash
cp prompt_engine/.env.example prompt_engine/.env
```

## Environment Variables

- `OPENAI_API_KEY`: required for OpenAI requests
- `OPENAI_MODEL`: optional, defaults to `gpt-4.1-mini`
- `LOG_LEVEL`: optional, defaults to `INFO`

## Running Examples

Run the examples from the repository root:

```bash
python -m prompt_engine.examples.run_classification_example
python -m prompt_engine.examples.run_summary_example
python -m prompt_engine.examples.run_extraction_example
python -m prompt_engine.examples.run_decision_example
```

Each example:

- loads sample input from `prompt_engine/examples/data/`
- builds context through the prompt engine
- validates JSON output when appropriate
- prints the result
- saves an evaluation record under `prompt_engine/evaluation_logs/`

## Running Tests

```bash
pytest prompt_engine/tests
```

## Extending The Toolkit

To add a new use case:

1. Create a new prompt template under a category in `prompt_engine/prompts/`
2. Prepare a structured input payload
3. Build a `PromptRequest` with the template name and input data
4. Enable JSON validation if the prompt is expected to return structured output
5. Add an example script or test if you want a reusable workflow

This keeps the framework general-purpose while letting future projects define their own domain-specific prompt assets.

## Evaluation Logging

The evaluator writes JSONL records into `prompt_engine/evaluation_logs/`. Each prompt name gets its own log file so you can capture outputs, notes, and scores over time.

## What Phase 2 Might Include

- Multiple LLM providers behind a shared interface
- Richer schema validation and typed extraction flows
- Prompt versioning and experiment tracking
- Batch execution and comparison tooling
- Multi-step prompt pipelines
