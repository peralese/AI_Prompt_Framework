from app.models import ExperimentRunResult
from app.report_generator import ExperimentReportGenerator


def test_report_generator_summarizes_results() -> None:
    generator = ExperimentReportGenerator()
    results = [
        ExperimentRunResult(
            experiment_name="summary_prompt_comparison",
            template_name="summarization/executive_summary",
            input_file="dataset.json",
            dataset_name="summary_dataset",
            case_id="case_1",
            input_payload={"project_name": "Customer Insights Dashboard"},
            validation_status="passed",
            scoring_status="scored",
            rubric_name="summary_rubric",
            rubric_score=4.0,
            rubric_max_score=5.0,
            rubric_breakdown=[
                {
                    "criterion_id": "executive_readability",
                    "description": "Executive readability",
                    "raw_score": 3,
                    "scale_max": 5,
                    "note": "Too verbose for an executive summary.",
                }
            ],
            raw_output="Summary one",
        ),
        ExperimentRunResult(
            experiment_name="summary_prompt_comparison",
            template_name="summarization/executive_summary_v2",
            input_file="dataset.json",
            dataset_name="summary_dataset",
            case_id="case_1",
            input_payload={"project_name": "Customer Insights Dashboard"},
            validation_status="passed",
            scoring_status="scored",
            rubric_name="summary_rubric",
            rubric_score=5.0,
            rubric_max_score=5.0,
            rubric_breakdown=[
                {
                    "criterion_id": "executive_readability",
                    "description": "Executive readability",
                    "raw_score": 5,
                    "scale_max": 5,
                    "note": "",
                }
            ],
            raw_output="Summary two",
        ),
    ]

    report = generator.generate_report("summary_prompt_comparison", results)

    assert report.best_template == "summarization/executive_summary_v2"
    assert report.total_runs == 2
    assert report.total_templates == 2
    assert report.total_cases == 1
    assert "Current best template" in report.markdown
    assert "summary_rubric" in report.markdown
    assert "executive_readability" in report.markdown
    assert "Readable Experiment Comparison" in report.readable_markdown
    assert "### Template: summarization/executive_summary_v2" in report.readable_markdown
    assert "```json" in report.readable_markdown
    assert "```text" in report.readable_markdown


def test_report_generator_records_notable_issues() -> None:
    generator = ExperimentReportGenerator()
    results = [
        ExperimentRunResult(
            experiment_name="summary_prompt_comparison",
            template_name="summarization/executive_summary",
            input_file="dataset.json",
            case_id="case_1",
            input_payload={"project_name": "Customer Insights Dashboard"},
            validation_status="failed",
            validation_error="Missing required key",
            run_status="failed",
            run_error="Prompt execution failed",
            scoring_status="skipped",
        )
    ]

    report = generator.generate_report("summary_prompt_comparison", results)

    assert any("failed" in issue.lower() for issue in report.notable_issues)
    assert "Notable Issues" in report.markdown


def test_report_generator_includes_notes_and_scores_in_readable_report() -> None:
    generator = ExperimentReportGenerator()
    results = [
        ExperimentRunResult(
            experiment_name="classification_comparison",
            template_name="classification/software_classifier",
            input_file="dataset.json",
            case_id="case_1",
            case_description="Classify a small tool list.",
            input_payload={"components": ["Redis", "PostgreSQL"]},
            notes="Baseline case for review.",
            validation_status="passed",
            rubric_name="classification_rubric",
            scoring_status="scored",
            rubric_score=3.0,
            rubric_max_score=4.0,
            rubric_breakdown=[
                {
                    "criterion_id": "classification_focus",
                    "description": "Classification focus",
                    "raw_score": 2,
                    "scale_max": 5,
                    "note": "Low confidence on one item.",
                }
            ],
            raw_output='{"items": [{"name": "Redis"}]}',
        )
    ]

    report = generator.generate_report("classification_comparison", results)

    assert "Baseline case for review." in report.readable_markdown
    assert "Rubric score: 3.0/4.0" in report.readable_markdown
    assert "Validation status: passed" in report.readable_markdown
    assert "classification_focus: 2/5" in report.readable_markdown
    assert "Low confidence on one item." in report.readable_markdown
