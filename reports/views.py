from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from students.models import StudentProfile
from .models import Report


# =========================================================
# LECTURER ACCESS CHECK
# =========================================================

def lecturer_only(request):

    return (
        request.user.is_superuser
        or hasattr(request.user, "lecturer_profile")
    )


# =========================================================
# REPORT LIST
# =========================================================

@login_required
def report_list(request):

    if not lecturer_only(request):
        return HttpResponse(
            "You do not have permission to access reports.",
            status=403
        )

    if request.user.is_superuser:

        reports = Report.objects.select_related(
            "assessment",
            "assessment__submission",
            "assessment__submission__assignment",
            "assessment__submission__assignment__student"
        ).order_by(
            "-created_at"
        )

    else:

        reports = Report.objects.select_related(
            "assessment",
            "assessment__submission",
            "assessment__submission__assignment",
            "assessment__submission__assignment__student"
        ).filter(
            assessment__submission__assignment__student__lecturer=(
                request.user.lecturer_profile
            )
        ).order_by(
            "-created_at"
        )

    return render(
        request,
        "reports/report_list.html",
        {
            "reports": reports
        }
    )


# =========================================================
# STUDENT-SPECIFIC REPORTS
# =========================================================

@login_required
def student_reports(request, student_id):

    if not lecturer_only(request):
        return HttpResponse(
            "You do not have permission to access reports.",
            status=403
        )

    # ---------------------------------------------------------
    # GET STUDENT
    # ---------------------------------------------------------

    if request.user.is_superuser:

        student = get_object_or_404(
            StudentProfile,
            id=student_id
        )

    else:

        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            lecturer=request.user.lecturer_profile
        )

    # ---------------------------------------------------------
    # GET REPORTS FOR THIS STUDENT
    # ---------------------------------------------------------

    reports = Report.objects.select_related(
        "assessment",
        "assessment__submission",
        "assessment__submission__assignment",
        "assessment__submission__assignment__student"
    ).filter(
        assessment__submission__assignment__student=student
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "reports/student_reports.html",
        {
            "student": student,
            "reports": reports
        }
    )


# =========================================================
# REPORT DETAIL
# =========================================================

@login_required
def report_detail(request, report_id):

    if not lecturer_only(request):
        return HttpResponse(
            "You do not have permission to access reports.",
            status=403
        )

    # ---------------------------------------------------------
    # GET REPORT
    # ---------------------------------------------------------

    if request.user.is_superuser:

        report = get_object_or_404(
            Report.objects.select_related(
                "assessment",
                "assessment__submission",
                "assessment__submission__assignment",
                "assessment__submission__assignment__student"
            ),
            id=report_id
        )

    else:

        report = get_object_or_404(
            Report.objects.select_related(
                "assessment",
                "assessment__submission",
                "assessment__submission__assignment",
                "assessment__submission__assignment__student"
            ),
            id=report_id,
            assessment__submission__assignment__student__lecturer=(
                request.user.lecturer_profile
            )
        )

    # ---------------------------------------------------------
    # GET RELATED INFORMATION
    # ---------------------------------------------------------

    assessment = report.assessment

    assignment = assessment.submission.assignment

    student = assignment.student

    # ---------------------------------------------------------
    # PREPARE CRITERION SCORES
    # ---------------------------------------------------------

    criterion_scores = []

    total_score = 0

    max_score = 0

    for criterion, details in (
        assessment.criterion_scores or {}
    ).items():

        if not isinstance(details, dict):
            continue

        # -----------------------------------------------------
        # SCORE
        # -----------------------------------------------------

        try:

            score = float(
                details.get(
                    "score",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            score = 0

        # -----------------------------------------------------
        # MAX SCORE
        # -----------------------------------------------------

        try:

            maximum = float(
                details.get(
                    "max_score",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            maximum = 0

        # -----------------------------------------------------
        # KEEP VALUES VALID
        # -----------------------------------------------------

        if score < 0:
            score = 0

        if maximum < 0:
            maximum = 0

        if maximum > 0 and score > maximum:
            score = maximum

        # -----------------------------------------------------
        # CALCULATE CRITERION PERCENTAGE
        # -----------------------------------------------------

        if maximum > 0:

            percentage = (
                score / maximum
            ) * 100

        else:

            percentage = 0

        # -----------------------------------------------------
        # CALCULATE TOTAL
        # -----------------------------------------------------

        total_score += score

        max_score += maximum

        # -----------------------------------------------------
        # ADD CRITERION
        # -----------------------------------------------------

        criterion_scores.append(
            {
                "name": criterion,

                "score": score,

                "max_score": maximum,

                "percentage": round(
                    percentage,
                    1
                ),

                "feedback": details.get(
                    "feedback",
                    "No feedback was provided."
                ),
            }
        )

    # ---------------------------------------------------------
    # OVERALL PERCENTAGE
    # ---------------------------------------------------------

    if max_score > 0:

        calculated_percentage = (
            total_score / max_score
        ) * 100

    else:

        calculated_percentage = 0

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------

    context = {

        "report": report,

        "assessment": assessment,

        "assignment": assignment,

        "student": student,

        "criterion_scores": criterion_scores,

        "total_score": round(
            total_score,
            2
        ),

        "max_score": round(
            max_score,
            2
        ),

        "calculated_percentage": round(
            calculated_percentage,
            2
        ),

        "strengths":
            assessment.strengths or [],

        "weaknesses":
            assessment.weaknesses or [],

        "citation_analysis":
            assessment.citation_analysis or {},

        "reference_analysis":
            assessment.reference_analysis or {},

        "grammar_analysis":
            assessment.grammar_analysis or {},

        "academic_writing_analysis":
            assessment.academic_writing_analysis or {},

        "feedback":
            assessment.feedback or "",
    }

    return render(
        request,
        "reports/report_detail.html",
        context
    )


# =========================================================
# DOWNLOAD REPORT AS PDF
# =========================================================

@login_required
def download_report(request, report_id):

    if not lecturer_only(request):
        return HttpResponse(
            "You do not have permission to download reports.",
            status=403
        )

    # ---------------------------------------------------------
    # GET REPORT
    # ---------------------------------------------------------

    if request.user.is_superuser:

        report = get_object_or_404(
            Report.objects.select_related(
                "assessment",
                "assessment__submission",
                "assessment__submission__assignment",
                "assessment__submission__assignment__student"
            ),
            id=report_id
        )

    else:

        report = get_object_or_404(
            Report.objects.select_related(
                "assessment",
                "assessment__submission",
                "assessment__submission__assignment",
                "assessment__submission__assignment__student"
            ),
            id=report_id,
            assessment__submission__assignment__student__lecturer=(
                request.user.lecturer_profile
            )
        )

    # ---------------------------------------------------------
    # RELATED INFORMATION
    # ---------------------------------------------------------

    assessment = report.assessment

    assignment = assessment.submission.assignment

    student = assignment.student

    # ---------------------------------------------------------
    # CALCULATE RAW SCORE
    # ---------------------------------------------------------

    total_score = 0

    max_score = 0

    criterion_scores = []

    for criterion, details in (
        assessment.criterion_scores or {}
    ).items():

        if not isinstance(details, dict):
            continue

        try:

            score = float(
                details.get(
                    "score",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            score = 0

        try:

            maximum = float(
                details.get(
                    "max_score",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            maximum = 0

        if score < 0:
            score = 0

        if maximum < 0:
            maximum = 0

        if maximum > 0 and score > maximum:
            score = maximum

        total_score += score

        max_score += maximum

        criterion_scores.append(
            (
                criterion,
                score,
                maximum
            )
        )

    # ---------------------------------------------------------
    # CALCULATE PERCENTAGE
    # ---------------------------------------------------------

    if max_score > 0:

        percentage = (
            total_score / max_score
        ) * 100

    else:

        percentage = 0

    # ---------------------------------------------------------
    # PDF RESPONSE
    # ---------------------------------------------------------

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        'attachment; '
        'filename="PepaGRADE_Assessment_Report.pdf"'
    )

    # ---------------------------------------------------------
    # PDF DOCUMENT
    # ---------------------------------------------------------

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=14,
        spaceAfter=18
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        spaceAfter=6
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=11
    )

    # ---------------------------------------------------------
    # SAFE TEXT FUNCTION
    # ---------------------------------------------------------

    def safe_text(value):

        if value is None:
            return ""

        return str(value)

    # ---------------------------------------------------------
    # LIST FUNCTION
    # ---------------------------------------------------------

    def add_list(story, items):

        if not items:
            story.append(
                Paragraph(
                    "None provided.",
                    normal_style
                )
            )
            return

        for item in items:

            story.append(
                Paragraph(
                    "• " + safe_text(item),
                    normal_style
                )
            )

    # ---------------------------------------------------------
    # STORY
    # ---------------------------------------------------------

    story = []

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "PepaGRADE DWU's Academic Writing Feedback Assistant",
            title_style
        )
    )

    story.append(
        Paragraph(
            "AI Assessment Report",
            subtitle_style
        )
    )

    # ---------------------------------------------------------
    # STUDENT INFORMATION
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Student Information",
            heading_style
        )
    )

    student_data = [
        [
            Paragraph(
                "<b>Student Name</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    student.full_name
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "<b>Student ID</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    student.student_id
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "<b>Program</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    student.program
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "<b>Year Level</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    student.year_level
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "<b>Assignment</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    assignment.title
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "<b>Document Type</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    assignment.document_type
                ),
                small_style
            )
        ],
    ]

    student_table = Table(
        student_data,
        colWidths=[
            130,
            350
        ]
    )

    student_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
            ]
        )
    )

    story.append(
        student_table
    )

    story.append(
        Spacer(
            1,
            12
        )
    )

    # ---------------------------------------------------------
    # OVERALL RESULT
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Overall Result",
            heading_style
        )
    )

    overall_data = [
        [
            Paragraph(
                "<b>Raw Score</b>",
                small_style
            ),
            Paragraph(
                f"{total_score:.2f} / {max_score:.2f}",
                small_style
            )
        ],
        [
            Paragraph(
                "<b>AI Grade</b>",
                small_style
            ),
            Paragraph(
                safe_text(
                    assessment.ai_grade
                ),
                small_style
            )
        ],
    ]

    overall_table = Table(
        overall_data,
        colWidths=[
            130,
            350
        ]
    )

    overall_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
            ]
        )
    )

    story.append(
        overall_table
    )

    story.append(
        Spacer(
            1,
            12
        )
    )

    # ---------------------------------------------------------
    # CRITERION SCORES
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Criterion Scores",
            heading_style
        )
    )

    criterion_data = [
        [
            Paragraph(
                "<b>Criterion</b>",
                small_style
            ),
            Paragraph(
                "<b>Score</b>",
                small_style
            ),
            Paragraph(
                "<b>Maximum</b>",
                small_style
            ),
            Paragraph(
                "<b>Percentage</b>",
                small_style
            ),
        ]
    ]

    for criterion, score, maximum in criterion_scores:

        if maximum > 0:

            criterion_percentage = (
                score / maximum
            ) * 100

        else:

            criterion_percentage = 0

        criterion_data.append(
            [
                Paragraph(
                    safe_text(criterion),
                    small_style
                ),
                Paragraph(
                    f"{score:.2f}",
                    small_style
                ),
                Paragraph(
                    f"{maximum:.2f}",
                    small_style
                ),
                Paragraph(
                    f"{criterion_percentage:.1f}%",
                    small_style
                ),
            ]
        )

    criterion_table = Table(
        criterion_data,
        colWidths=[
            230,
            80,
            80,
            90
        ]
    )

    criterion_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    story.append(
        criterion_table
    )

    # ---------------------------------------------------------
    # CITATION ANALYSIS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Citation Analysis",
            heading_style
        )
    )

    citation = assessment.citation_analysis or {}

    citation_data = [
        [
            Paragraph(
                "<b>Item</b>",
                small_style
            ),
            Paragraph(
                "<b>Result</b>",
                small_style
            )
        ],
        [
            Paragraph(
                "Citations Found",
                small_style
            ),
            Paragraph(
                safe_text(
                    citation.get(
                        "citations_found",
                        citation.get(
                            "found",
                            0
                        )
                    )
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "Matched Citations",
                small_style
            ),
            Paragraph(
                safe_text(
                    citation.get(
                        "matched",
                        0
                    )
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "Unmatched Citations",
                small_style
            ),
            Paragraph(
                safe_text(
                    citation.get(
                        "unmatched",
                        0
                    )
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "Uncited Sources",
                small_style
            ),
            Paragraph(
                safe_text(
                    citation.get(
                        "uncited",
                        0
                    )
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "Observation",
                small_style
            ),
            Paragraph(
                safe_text(
                    citation.get(
                        "observation",
                        "No observation provided."
                    )
                ),
                small_style
            )
        ],
    ]

    citation_table = Table(
        citation_data,
        colWidths=[
            170,
            310
        ]
    )

    citation_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    story.append(
        citation_table
    )

    # ---------------------------------------------------------
    # REFERENCE ANALYSIS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Reference Analysis",
            heading_style
        )
    )

    reference = assessment.reference_analysis or {}

    reference_data = [
        [
            Paragraph(
                "<b>Item</b>",
                small_style
            ),
            Paragraph(
                "<b>Result</b>",
                small_style
            )
        ],
        [
            Paragraph(
                "References Found",
                small_style
            ),
            Paragraph(
                safe_text(
                    reference.get(
                        "references_found",
                        reference.get(
                            "found",
                            0
                        )
                    )
                ),
                small_style
            )
        ],
        [
            Paragraph(
                "Observation",
                small_style
            ),
            Paragraph(
                safe_text(
                    reference.get(
                        "observation",
                        "No observation provided."
                    )
                ),
                small_style
            )
        ],
    ]

    reference_table = Table(
        reference_data,
        colWidths=[
            170,
            310
        ]
    )

    reference_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ]
        )
    )

    story.append(
        reference_table
    )

    # ---------------------------------------------------------
    # GRAMMAR ANALYSIS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Grammar Analysis",
            heading_style
        )
    )

    grammar = assessment.grammar_analysis or {}

    grammar_observation = grammar.get(
        "observation",
        grammar.get(
            "feedback",
            "No grammar analysis was provided."
        )
    )

    story.append(
        Paragraph(
            safe_text(
                grammar_observation
            ),
            normal_style
        )
    )

    # ---------------------------------------------------------
    # ACADEMIC WRITING ANALYSIS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Academic Writing Analysis",
            heading_style
        )
    )

    academic_writing = (
        assessment.academic_writing_analysis
        or {}
    )

    academic_writing_observation = (
        academic_writing.get(
            "observation",
            academic_writing.get(
                "feedback",
                "No academic writing analysis was provided."
            )
        )
    )

    story.append(
        Paragraph(
            safe_text(
                academic_writing_observation
            ),
            normal_style
        )
    )

    # ---------------------------------------------------------
    # STRENGTHS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Strengths",
            heading_style
        )
    )

    add_list(
        story,
        assessment.strengths or []
    )

    # ---------------------------------------------------------
    # WEAKNESSES
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Areas for Improvement",
            heading_style
        )
    )

    add_list(
        story,
        assessment.weaknesses or []
    )

    # ---------------------------------------------------------
    # OVERALL FEEDBACK
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Overall Feedback",
            heading_style
        )
    )

    story.append(
        Paragraph(
            safe_text(
                assessment.feedback
                or "No overall feedback was provided."
            ),
            normal_style
        )
    )

    # ---------------------------------------------------------
    # DISCLAIMER
    # ---------------------------------------------------------

    story.append(
        Spacer(
            1,
            18
        )
    )

    story.append(
        Paragraph(
            "This report was generated by PepaGRADE. "
            "The AI assessment is intended to support lecturer "
            "review and does not replace the lecturer's academic "
            "judgment.",
            small_style
        )
    )

    # ---------------------------------------------------------
    # BUILD PDF
    # ---------------------------------------------------------

    doc.build(
        story
    )

    return response