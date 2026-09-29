
from django.db.models.signals import post_save
from django.dispatch import receiver

from assessment.models import Assessment
from .models import Report


@receiver(post_save, sender=Assessment)
def create_or_update_report(sender, instance, created, **kwargs):

    submission = instance.submission
    assignment = submission.assignment
    student = assignment.student

    ai_score = instance.ai_score
    ai_grade = instance.ai_grade

    criterion_scores = instance.criterion_scores or {}
    strengths = instance.strengths or []
    weaknesses = instance.weaknesses or []

    # ---------------------------------------------------------
    # BUILD REPORT CONTENT
    # ---------------------------------------------------------

    report_content = []

    report_content.append("PEPAGRADE ASSESSMENT REPORT")
    report_content.append("=" * 60)
    report_content.append("")

    # ---------------------------------------------------------
    # STUDENT INFORMATION
    # ---------------------------------------------------------

    report_content.append("STUDENT INFORMATION")
    report_content.append("-" * 60)

    report_content.append(
        f"Student Name: {student.full_name}"
    )

    report_content.append(
        f"Student ID: {student.student_id}"
    )

    report_content.append(
        f"Program: {student.program}"
    )

    report_content.append(
        f"Year Level: Year {student.year_level}"
    )

    report_content.append("")

    # ---------------------------------------------------------
    # ASSIGNMENT INFORMATION
    # ---------------------------------------------------------

    report_content.append("ASSIGNMENT INFORMATION")
    report_content.append("-" * 60)

    report_content.append(
        f"Assignment: {assignment.title}"
    )

    report_content.append(
        f"Document Type: {assignment.get_document_type_display()}"
    )

    report_content.append("")

    # ---------------------------------------------------------
    # AI ASSESSMENT RESULT
    # ---------------------------------------------------------

    report_content.append("AI ASSESSMENT RESULT")
    report_content.append("-" * 60)

    if ai_score is not None:
        report_content.append(
            f"AI Score: {float(ai_score):.1f}%"
        )
    else:
        report_content.append(
            "AI Score: Not available"
        )

    report_content.append(
        f"AI Grade: {ai_grade if ai_grade else 'Not available'}"
    )

    report_content.append("")

    # ---------------------------------------------------------
    # CRITERION SCORES
    # ---------------------------------------------------------

    report_content.append("CRITERION SCORES")
    report_content.append("-" * 60)

    if criterion_scores:

        total_score = 0
        max_score = 0

        for criterion, details in criterion_scores.items():

            if not isinstance(details, dict):
                continue

            try:
                score = float(details.get("score", 0))
            except (TypeError, ValueError):
                score = 0

            try:
                maximum = float(details.get("max_score", 0))
            except (TypeError, ValueError):
                maximum = 0

            if score < 0:
                score = 0

            if maximum < 0:
                maximum = 0

            if maximum > 0 and score > maximum:
                score = maximum

            if maximum > 0:
                percentage = (score / maximum) * 100
            else:
                percentage = 0

            total_score += score
            max_score += maximum

            report_content.append(
                f"{criterion}"
            )

            report_content.append(
                f"  Score: {score:.1f}/{maximum:.1f}"
            )

            report_content.append(
                f"  Percentage: {percentage:.1f}%"
            )

            feedback = details.get(
                "feedback",
                "No feedback provided."
            )

            report_content.append(
                f"  Feedback: {feedback}"
            )

            report_content.append("")

        if max_score > 0:
            overall_percentage = (
                total_score / max_score
            ) * 100
        else:
            overall_percentage = 0

        report_content.append(
            f"TOTAL SCORE: {total_score:.1f}/{max_score:.1f}"
        )

        report_content.append(
            f"OVERALL PERCENTAGE: {overall_percentage:.1f}%"
        )

    else:

        report_content.append(
            "No criterion scores available."
        )

    report_content.append("")

    # ---------------------------------------------------------
    # STRENGTHS
    # ---------------------------------------------------------

    report_content.append("STRENGTHS")
    report_content.append("-" * 60)

    if strengths:

        for strength in strengths:
            report_content.append(
                f"• {strength}"
            )

    else:

        report_content.append(
            "No strengths recorded."
        )

    report_content.append("")

    # ---------------------------------------------------------
    # AREAS FOR IMPROVEMENT
    # ---------------------------------------------------------

    report_content.append("AREAS FOR IMPROVEMENT")
    report_content.append("-" * 60)

    if weaknesses:

        for weakness in weaknesses:
            report_content.append(
                f"• {weakness}"
            )

    else:

        report_content.append(
            "No areas for improvement recorded."
        )

    report_content.append("")

    # ---------------------------------------------------------
    # CITATION ANALYSIS
    # ---------------------------------------------------------

    citation_analysis = instance.citation_analysis or {}

    report_content.append("CITATION ANALYSIS")
    report_content.append("-" * 60)

    report_content.append(
        f"In-text Citations Found: "
        f"{citation_analysis.get('in_text_citations_found', 0)}"
    )

    report_content.append(
        f"Matched References: "
        f"{citation_analysis.get('matched_references', 0)}"
    )

    report_content.append(
        f"Unmatched Citations: "
        f"{citation_analysis.get('unmatched_citations', 0)}"
    )

    report_content.append(
        f"Uncited References: "
        f"{citation_analysis.get('uncited_references', 0)}"
    )

    if citation_analysis.get("citation_issues"):

        report_content.append("")
        report_content.append("Citation Issues:")

        for issue in citation_analysis["citation_issues"]:
            report_content.append(
                f"• {issue}"
            )

    if citation_analysis.get("overall_observation"):

        report_content.append("")
        report_content.append(
            "Overall Observation:"
        )

        report_content.append(
            citation_analysis["overall_observation"]
        )

    report_content.append("")

    # ---------------------------------------------------------
    # REFERENCE ANALYSIS
    # ---------------------------------------------------------

    reference_analysis = instance.reference_analysis or {}

    report_content.append("REFERENCE ANALYSIS")
    report_content.append("-" * 60)

    report_content.append(
        f"References Found: "
        f"{reference_analysis.get('references_found', 0)}"
    )

    if reference_analysis.get(
        "missing_or_incomplete_references"
    ):

        report_content.append("")
        report_content.append(
            "Missing or Incomplete References:"
        )

        for item in reference_analysis[
            "missing_or_incomplete_references"
        ]:

            report_content.append(
                f"• {item}"
            )

    if reference_analysis.get("formatting_issues"):

        report_content.append("")
        report_content.append(
            "Formatting Issues:"
        )

        for item in reference_analysis[
            "formatting_issues"
        ]:

            report_content.append(
                f"• {item}"
            )

    if reference_analysis.get("overall_observation"):

        report_content.append("")
        report_content.append(
            "Overall Observation:"
        )

        report_content.append(
            reference_analysis["overall_observation"]
        )

    report_content.append("")

    # ---------------------------------------------------------
    # GRAMMAR ANALYSIS
    # ---------------------------------------------------------

    grammar_analysis = instance.grammar_analysis or {}

    report_content.append("GRAMMAR AND SPELLING ANALYSIS")
    report_content.append("-" * 60)

    if grammar_analysis.get("grammar_issues"):

        report_content.append("Grammar Issues:")

        for issue in grammar_analysis["grammar_issues"]:
            report_content.append(
                f"• {issue}"
            )

        report_content.append("")

    if grammar_analysis.get("spelling_issues"):

        report_content.append("Spelling Issues:")

        for issue in grammar_analysis["spelling_issues"]:
            report_content.append(
                f"• {issue}"
            )

        report_content.append("")

    if grammar_analysis.get("punctuation_issues"):

        report_content.append("Punctuation Issues:")

        for issue in grammar_analysis["punctuation_issues"]:
            report_content.append(
                f"• {issue}"
            )

        report_content.append("")

    if grammar_analysis.get("overall_observation"):

        report_content.append(
            "Overall Observation:"
        )

        report_content.append(
            grammar_analysis["overall_observation"]
        )

    report_content.append("")



    # ---------------------------------------------------------
    # AI FEEDBACK
    # ---------------------------------------------------------

    report_content.append("AI FEEDBACK")
    report_content.append("-" * 60)

    report_content.append(
        instance.feedback
        if instance.feedback
        else "No AI feedback available."
    )

    report_content.append("")

    # ---------------------------------------------------------
    # LECTURER REVIEW
    # ---------------------------------------------------------

    if instance.is_reviewed:

        report_content.append("LECTURER REVIEW")
        report_content.append("-" * 60)

        report_content.append(
            "Lecturer Score: "
            + (
                str(instance.lecturer_score)
                if instance.lecturer_score is not None
                else "Not provided"
            )
        )

        report_content.append("")

        report_content.append(
            "Lecturer Feedback:"
        )

        report_content.append(
            instance.lecturer_feedback
            if instance.lecturer_feedback
            else "No lecturer feedback provided."
        )

    # ---------------------------------------------------------
    # SAVE REPORT
    # ---------------------------------------------------------

    Report.objects.update_or_create(
        assessment=instance,
        defaults={
            "title": (
                f"Assessment Report - "
                f"{student.full_name} - "
                f"{assignment.title}"
            ),
            "report_content": "\n".join(
                report_content
            ).strip(),
        }
    )

