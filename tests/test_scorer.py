import json
from pathlib import Path

from app.models import ExperimentRunResult
from app.rubric_loader import RubricLoader
from app.scorer import ExperimentScorer


def _load_summary_rubric() -> object:
    rubric_path = (
        Path(__file__).resolve().parent.parent
        / "rubrics"
        / "summary_quality_rubric.json"
    )
    rubric, _ = RubricLoader().load(rubric_path)
    return rubric


def test_dense_summary_scores_lower_than_executive_friendly_summary() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Customer Insights Dashboard",
        "status": "In delivery",
        "risks": [
            "Two upstream data sources still have inconsistent field mapping",
            "The analytics team has limited bandwidth for late-cycle changes",
        ],
        "next_actions": [
            "Finalize source mapping rules",
            "Complete UAT checklist",
        ],
    }

    dense_output = (
        "Customer Insights Dashboard remains in delivery with the pipeline, mapping, "
        "schema, integration, and deployment work still moving through staging, and the "
        "team continues to process detailed technical dependencies across multiple systems "
        "while documenting validation conditions, timing assumptions, source irregularities, "
        "and supporting review mechanics that affect cross-functional reporting."
    )
    executive_output = (
        "Customer Insights Dashboard is in delivery, with core work moving forward in staging. "
        "The main risk is inconsistent source mapping and limited analytics bandwidth.\n\n"
        "The immediate focus is to finalize mapping rules and complete the UAT checklist so the "
        "team can keep the rollout on schedule."
    )

    dense_score, dense_max, _ = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=dense_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    executive_score, executive_max, _ = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=executive_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    assert dense_max == executive_max
    assert executive_score > dense_score


def test_summary_missing_risks_scores_lower_when_risks_are_present() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Workflow Automation Pilot",
        "status": "Planning complete",
        "risks": [
            "Source system API rate limits may affect batch processing",
        ],
        "next_actions": [
            "Finalize the pilot scope",
        ],
    }

    missing_risk_output = (
        "Workflow Automation Pilot is in planning complete status. The team is aligned "
        "and ready to finalize scope.\n\nThe next focus is to confirm ownership and move "
        "into implementation."
    )
    risk_output = (
        "Workflow Automation Pilot is planning complete, but API rate limits remain a key "
        "risk for the batch design.\n\nThe next step is to finalize scope and confirm ownership "
        "before implementation starts."
    )

    missing_risk_score, _, missing_breakdown = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=missing_risk_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    risk_score, _, _ = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=risk_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    risk_dimension = next(
        item for item in missing_breakdown if item["criterion_id"] == "risk_identification"
    )
    assert missing_risk_score < risk_score
    assert risk_dimension["raw_score"] < risk_dimension["scale_max"]


def test_summary_missing_next_actions_scores_lower_when_actions_are_present() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Regional Operations Review",
        "status": "In progress",
        "risks": [
            "A delayed review cycle could compress the final approval window",
        ],
        "next_actions": [
            "Collect the remaining source documents",
            "Confirm the final review date",
        ],
    }

    no_actions_output = (
        "Regional Operations Review is in progress, and the approval timeline remains the main "
        "risk because the review cycle could slip."
    )
    with_actions_output = (
        "Regional Operations Review is in progress, with the approval window still at risk if the "
        "review cycle slips.\n\nThe immediate next steps are to collect the remaining source "
        "documents and confirm the final review date."
    )

    no_actions_score, _, no_actions_breakdown = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=no_actions_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    with_actions_score, _, _ = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=with_actions_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    action_dimension = next(
        item for item in no_actions_breakdown if item["criterion_id"] == "actionability"
    )
    assert no_actions_score < with_actions_score
    assert action_dimension["raw_score"] < action_dimension["scale_max"]
    assert action_dimension["note"] is not None


def test_structure_sensitive_summary_scores_higher_for_better_structure() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Customer Insights Dashboard",
        "status": "In delivery",
        "risks": ["Two upstream data sources still have inconsistent field mapping"],
        "next_actions": ["Finalize source mapping rules"],
    }

    unstructured_output = (
        "The team should finalize source mapping rules soon. Two upstream data sources still "
        "have inconsistent field mapping. Customer Insights Dashboard is in delivery."
    )
    structured_output = (
        "Customer Insights Dashboard is in delivery, with the main issue still centered on "
        "inconsistent source mapping.\n\nThe immediate next step is to finalize the mapping rules."
    )

    unstructured_score, _, unstructured_breakdown = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=unstructured_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    structured_score, _, _ = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=structured_output,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    structure_dimension = next(
        item
        for item in unstructured_breakdown
        if item["criterion_id"] == "structure_and_instruction_adherence"
    )
    assert structured_score > unstructured_score
    assert structure_dimension["raw_score"] < structure_dimension["scale_max"]


def test_summary_calibration_paragraph_vs_explicit_actions_vs_structured() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Regional Operations Review",
        "status": "In progress",
        "highlights": [
            "Field teams completed the first wave of site reviews",
            "The reporting draft is ready for stakeholder feedback",
        ],
        "risks": [
            "Two source documents from partner teams are still pending",
            "A delayed review cycle could compress the final approval window",
        ],
        "next_actions": [
            "Collect the remaining source documents",
            "Incorporate stakeholder feedback into the draft",
            "Confirm the final review date",
        ],
    }

    summary_a = (
        "Regional Operations Review is in progress, with site reviews completed and the draft ready "
        "for feedback. The approval window could tighten if the review cycle slips."
    )
    summary_b = (
        "Regional Operations Review is in progress, with the draft ready for stakeholder feedback. "
        "The main risk is that delayed partner documents could compress the approval window.\n\n"
        "The next steps are to collect the remaining documents, incorporate feedback into the draft, "
        "and confirm the final review date."
    )
    summary_c = (
        "Regional Operations Review is in progress, with site reviews complete and the draft ready "
        "for stakeholder feedback.\n\n"
        "- Risk: delayed partner documents could compress the approval window.\n"
        "- Next steps: collect the remaining documents, incorporate stakeholder feedback, and confirm the final review date."
    )

    score_a, _, breakdown_a = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=summary_a,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    score_b, _, breakdown_b = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=summary_b,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    score_c, _, breakdown_c = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v3",
            input_file="input.json",
            raw_output=summary_c,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    actionability_a = next(
        item for item in breakdown_a if item["criterion_id"] == "actionability"
    )
    actionability_b = next(
        item for item in breakdown_b if item["criterion_id"] == "actionability"
    )
    readability_b = next(
        item for item in breakdown_b if item["criterion_id"] == "executive_readability"
    )
    readability_c = next(
        item for item in breakdown_c if item["criterion_id"] == "executive_readability"
    )

    assert score_a < score_b < score_c
    assert actionability_a["raw_score"] <= 3
    assert actionability_b["raw_score"] > actionability_a["raw_score"]
    assert readability_c["raw_score"] >= readability_b["raw_score"]


def test_actionability_calibration_orders_none_vague_and_explicit_next_steps() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Platform Migration Review",
        "status": "Under review",
        "highlights": [
            "The migration plan is ready for leadership review",
        ],
        "risks": [
            "A dependency on the identity workstream could delay approval",
        ],
        "next_actions": [
            "Confirm the identity dependency timeline",
            "Prepare the approval package",
            "Set the steering committee review date",
        ],
    }

    summary_a = (
        "Platform Migration Review is under review, and the main dependency remains the identity "
        "workstream timeline."
    )
    summary_b = (
        "Platform Migration Review is under review, with the identity dependency still affecting "
        "timing. The team should keep the approval package moving and align on the review date."
    )
    summary_c = (
        "Platform Migration Review is under review, with the identity dependency still affecting "
        "timing.\n\nNext Steps:\n"
        "- Analytics lead should confirm the identity dependency timeline.\n"
        "- PM should prepare the approval package.\n"
        "- Operations should set the steering committee review date by priority for this week."
    )

    _, _, breakdown_a = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=summary_a,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    _, _, breakdown_b = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=summary_b,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    _, _, breakdown_c = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v3",
            input_file="input.json",
            raw_output=summary_c,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    actionability_a = next(
        item for item in breakdown_a if item["criterion_id"] == "actionability"
    )
    actionability_b = next(
        item for item in breakdown_b if item["criterion_id"] == "actionability"
    )
    actionability_c = next(
        item for item in breakdown_c if item["criterion_id"] == "actionability"
    )

    assert actionability_a["raw_score"] < actionability_b["raw_score"] < actionability_c["raw_score"]
    assert actionability_a["raw_score"] == 1
    assert actionability_b["raw_score"] <= 3
    assert actionability_c["raw_score"] >= 4


def test_signal_vs_noise_calibration_scores_noisy_summary_below_focused_summary() -> None:
    scorer = ExperimentScorer()
    rubric = _load_summary_rubric()
    input_payload = {
        "project_name": "Pricing Engine Refresh",
        "status": "Under review",
        "highlights": [
            "Leadership is deciding whether to continue the refresh this quarter",
        ],
        "risks": [
            "The identity service dependency is still unresolved",
        ],
        "next_actions": [
            "Confirm the dependency timeline",
        ],
    }

    noisy_summary = (
        "Pricing Engine Refresh is under review while the server, database, API, schema, "
        "deployment, pipeline, integration, and latency work continue across staging and "
        "validation. Multiple technical tracks, mapping reviews, handoff mechanics, and "
        "infrastructure details are still being documented across several systems while the "
        "team works through supporting implementation conditions."
    )
    focused_summary = (
        "Pricing Engine Refresh is under review, and leadership still needs to decide whether "
        "to continue this quarter. The main dependency is the unresolved identity service "
        "timeline, which could delay the decision."
    )

    _, _, noisy_breakdown = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary",
            input_file="input.json",
            raw_output=noisy_summary,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )
    _, _, focused_breakdown = scorer.score_run(
        ExperimentRunResult(
            experiment_name="summary_test",
            template_name="summarization/executive_summary_v2",
            input_file="input.json",
            raw_output=focused_summary,
            validation_status="not_requested",
        ),
        input_payload=input_payload,
        rubric=rubric,
    )

    noisy_signal = next(
        item for item in noisy_breakdown if item["criterion_id"] == "signal_vs_noise"
    )
    focused_signal = next(
        item for item in focused_breakdown if item["criterion_id"] == "signal_vs_noise"
    )

    assert noisy_signal["raw_score"] < focused_signal["raw_score"]
    assert focused_signal["raw_score"] >= 2
