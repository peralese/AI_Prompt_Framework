"""Human-readable experiment summary generation."""

from __future__ import annotations

from collections import defaultdict
import json

from .models import ExperimentReport, ExperimentRunResult, TemplateFinding


class ExperimentReportGenerator:
    """Generate human-readable findings from experiment results."""

    def generate_report(
        self, experiment_name: str, results: list[ExperimentRunResult]
    ) -> ExperimentReport:
        """Build a markdown report from experiment results."""

        if not results:
            markdown = f"# Experiment Report\n\nNo results were available for `{experiment_name}`."
            return ExperimentReport(
                experiment_name=experiment_name,
                total_runs=0,
                total_templates=0,
                total_cases=0,
                markdown=markdown,
            )

        grouped_results: dict[str, list[ExperimentRunResult]] = defaultdict(list)
        for result in results:
            grouped_results[result.template_name].append(result)

        findings = [
            self._summarize_template(template_name, template_results)
            for template_name, template_results in sorted(grouped_results.items())
        ]
        best_template = self._select_best_template(findings)
        notable_issues = self._collect_notable_issues(results)
        dataset_name = next((result.dataset_name for result in results if result.dataset_name), None)
        rubric_name = next((result.rubric_name for result in results if result.rubric_name), None)
        total_cases = len({result.case_id for result in results if result.case_id}) or 1

        report = ExperimentReport(
            experiment_name=experiment_name,
            dataset_name=dataset_name,
            rubric_name=rubric_name,
            total_runs=len(results),
            total_templates=len(grouped_results),
            total_cases=total_cases,
            best_template=best_template,
            findings=findings,
            notable_issues=notable_issues,
            markdown="",
            readable_markdown="",
        )
        report.markdown = self._render_markdown(report)
        report.readable_markdown = self._render_readable_markdown(report, results)
        return report

    def _summarize_template(
        self, template_name: str, results: list[ExperimentRunResult]
    ) -> TemplateFinding:
        """Aggregate findings for one template across runs."""

        run_count = len(results)
        completed = sum(result.run_status == "completed" for result in results)
        completion_rate = completed / run_count if run_count else 0.0

        validation_requested = [
            result for result in results if result.validation_status != "not_requested"
        ]
        validation_pass_rate = None
        if validation_requested:
            validation_pass_rate = (
                sum(result.validation_status == "passed" for result in validation_requested)
                / len(validation_requested)
            )

        scored_results = [
            result
            for result in results
            if result.scoring_status == "scored"
            and result.rubric_score is not None
            and result.rubric_max_score
        ]
        average_score = None
        if scored_results:
            average_score = sum(
                result.rubric_score / result.rubric_max_score for result in scored_results
            ) / len(scored_results)

        strengths: list[str] = []
        concerns: list[str] = []
        if completion_rate == 1.0:
            strengths.append("Completed all assigned runs.")
        elif completion_rate < 1.0:
            concerns.append("Did not complete every assigned run.")

        if validation_pass_rate is not None:
            if validation_pass_rate == 1.0:
                strengths.append("Passed validation on all validated runs.")
            elif validation_pass_rate < 1.0:
                concerns.append("Had at least one validation failure.")

        if average_score is not None:
            if average_score >= 0.8:
                strengths.append(f"Achieved a strong average rubric score of {average_score:.0%}.")
            elif average_score < 0.6:
                concerns.append(f"Average rubric score was {average_score:.0%}.")

        if not strengths:
            strengths.append("Produced usable output for comparison.")

        return TemplateFinding(
            template_name=template_name,
            run_count=run_count,
            completion_rate=completion_rate,
            validation_pass_rate=validation_pass_rate,
            average_score=average_score,
            strengths=strengths,
            concerns=concerns,
        )

    def _select_best_template(self, findings: list[TemplateFinding]) -> str | None:
        """Select the current best template from aggregated findings."""

        if not findings:
            return None

        def sort_key(finding: TemplateFinding) -> tuple[float, float, float]:
            return (
                finding.average_score if finding.average_score is not None else -1.0,
                finding.validation_pass_rate if finding.validation_pass_rate is not None else -1.0,
                finding.completion_rate,
            )

        return max(findings, key=sort_key).template_name

    def _collect_notable_issues(self, results: list[ExperimentRunResult]) -> list[str]:
        """Collect concise notable issues from experiment runs."""

        issues: list[str] = []
        run_failures = [result for result in results if result.run_status == "failed"]
        validation_failures = [
            result for result in results if result.validation_status == "failed"
        ]
        scoring_failures = [result for result in results if result.scoring_status == "failed"]

        if run_failures:
            issues.append(f"{len(run_failures)} run(s) failed before completion.")
        if validation_failures:
            issues.append(f"{len(validation_failures)} run(s) failed validation.")
        if scoring_failures:
            issues.append(f"{len(scoring_failures)} run(s) could not be scored.")
        if not issues:
            issues.append("No major execution, validation, or scoring issues were detected.")

        return issues

    def _render_markdown(self, report: ExperimentReport) -> str:
        """Render a markdown experiment summary."""

        lines = [
            f"# Experiment Report: {report.experiment_name}",
            "",
            "## Overview",
            f"- Total runs: {report.total_runs}",
            f"- Templates compared: {report.total_templates}",
            f"- Cases covered: {report.total_cases}",
        ]
        if report.dataset_name:
            lines.append(f"- Dataset: {report.dataset_name}")
        if report.rubric_name:
            lines.append(f"- Rubric: {report.rubric_name}")
        if report.best_template:
            lines.append(f"- Current best template: `{report.best_template}`")

        lines.extend(["", "## Findings"])
        for finding in report.findings:
            lines.append(f"### {finding.template_name}")
            lines.append(f"- Runs: {finding.run_count}")
            lines.append(f"- Completion rate: {finding.completion_rate:.0%}")
            if finding.validation_pass_rate is not None:
                lines.append(f"- Validation pass rate: {finding.validation_pass_rate:.0%}")
            if finding.average_score is not None:
                lines.append(f"- Average rubric score: {finding.average_score:.0%}")
            lines.append(f"- Strengths: {' '.join(finding.strengths)}")
            if finding.concerns:
                lines.append(f"- Concerns: {' '.join(finding.concerns)}")
            else:
                lines.append("- Concerns: No major concerns noted.")

        lines.extend(["", "## Notable Issues"])
        for issue in report.notable_issues:
            lines.append(f"- {issue}")

        return "\n".join(lines)

    def _render_readable_markdown(
        self, report: ExperimentReport, results: list[ExperimentRunResult]
    ) -> str:
        """Render a readable side-by-side comparison report grouped by case."""

        case_groups: dict[str, list[ExperimentRunResult]] = defaultdict(list)
        case_order: list[str] = []
        for result in results:
            case_key = result.case_id or "input_1"
            if case_key not in case_groups:
                case_order.append(case_key)
            case_groups[case_key].append(result)

        lines = [
            f"# Readable Experiment Comparison: {report.experiment_name}",
            "",
        ]
        if report.dataset_name:
            lines.append(f"- Dataset: {report.dataset_name}")
        if report.rubric_name:
            lines.append(f"- Rubric: {report.rubric_name}")
        lines.extend(
            [
                f"- Cases covered: {report.total_cases}",
                f"- Templates compared: {report.total_templates}",
                "",
            ]
        )

        for index, case_key in enumerate(case_order, start=1):
            case_results = sorted(
                case_groups[case_key], key=lambda result: result.template_name
            )
            case_sample = case_results[0]
            lines.append(f"## Case {index}: {case_key}")
            if case_sample.case_description:
                lines.append(case_sample.case_description)
                lines.append("")
            lines.append("### Input")
            input_payload = case_sample.input_payload or {}
            lines.append("```json")
            lines.append(json.dumps(input_payload, indent=2, sort_keys=True))
            lines.append("```")
            if case_sample.notes:
                lines.append("")
                lines.append(f"Notes: {case_sample.notes}")
            lines.append("")

            for result in case_results:
                lines.append(f"### Template: {result.template_name}")
                lines.append(f"- Validation status: {result.validation_status}")
                if result.validation_error:
                    lines.append(f"- Validation error: {result.validation_error}")
                if result.rubric_score is not None and result.rubric_max_score is not None:
                    lines.append(
                        f"- Rubric score: {result.rubric_score}/{result.rubric_max_score}"
                    )
                elif result.scoring_status != "not_requested":
                    lines.append(f"- Scoring status: {result.scoring_status}")
                if result.notes:
                    lines.append(f"- Notes: {result.notes}")
                lines.append("- Output:")
                lines.append("```text")
                lines.append((result.raw_output or "").strip())
                lines.append("```")
                lines.append("")

        return "\n".join(lines).strip()
