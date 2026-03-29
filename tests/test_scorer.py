from app.models import EvaluationRubric, ExperimentRunResult, RubricCriterion
from app.scorer import ExperimentScorer


def test_scorer_applies_generic_rubric_rules() -> None:
    scorer = ExperimentScorer()
    run_result = ExperimentRunResult(
        experiment_name="summary_experiment",
        template_name="summarization/executive_summary",
        input_file="input.json",
        raw_output="Customer Insights Dashboard is in delivery. Key risks remain around source mapping.",
        validation_status="not_requested",
    )
    rubric = EvaluationRubric(
        rubric_name="summary_rubric",
        criteria=[
            RubricCriterion(
                criterion_id="non_empty",
                description="Output must not be empty.",
                rule_type="non_empty_output",
                weight=1.0,
            ),
            RubricCriterion(
                criterion_id="context",
                description="Output should mention project context.",
                rule_type="contains_any_input_values",
                weight=2.0,
                config={"input_keys": ["project_name", "status"]},
            ),
            RubricCriterion(
                criterion_id="risk",
                description="Output should mention risk.",
                rule_type="contains_all_strings",
                weight=1.0,
                config={"strings": ["risk"]},
            ),
        ],
    )

    score, max_score, breakdown = scorer.score_run(
        run_result=run_result,
        input_payload={
            "project_name": "Customer Insights Dashboard",
            "status": "In delivery",
        },
        rubric=rubric,
    )

    assert score == 4.0
    assert max_score == 4.0
    assert len(breakdown) == 3
    assert all(item["passed"] for item in breakdown)
