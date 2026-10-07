
import json
import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from assignments.models import (
    Assignment,
    AssignmentSubmission,
    MarkingGuide,
)

from students.models import StudentProfile

from .forms import AIAssessmentForm
from .models import Assessment

from .services.ai_assessment import (
    assess_submission,
    AIAssessmentError,
)

from assignments.services.document_parser import extract_text


logger = logging.getLogger(__name__)


# =========================================================
# HELPER: CHECK AJAX REQUEST
# =========================================================

def is_ajax_request(request):
    """
    Check whether the request was made using AJAX/fetch.
    """

    return (
        request.headers.get(
            'x-requested-with'
        ) == 'XMLHttpRequest'
    )


# =========================================================
# HELPER: CONVERT AI RESPONSE TO DICTIONARY
# =========================================================

def normalize_ai_result(result):
    """
    Make sure the AI result is a Python dictionary.

    Gemini or Mistral may sometimes return JSON as a string
    instead of returning an actual Python dictionary.
    """

    # Already a dictionary
    if isinstance(result, dict):
        return result

    # AI returned JSON as a string
    if isinstance(result, str):

        result = result.strip()

        # Remove Markdown code fences
        if result.startswith('```json'):
            result = result[7:]

        elif result.startswith('```'):
            result = result[3:]

        if result.endswith('```'):
            result = result[:-3]

        result = result.strip()

        try:

            parsed_result = json.loads(result)

        except json.JSONDecodeError as error:

            raise ValueError(
                'The AI returned an invalid response. '
                'Please try the assessment again.'
            ) from error

        if not isinstance(parsed_result, dict):

            raise ValueError(
                'The AI response was not in the expected format.'
            )

        return parsed_result

    raise ValueError(
        'The AI returned an unexpected response format.'
    )


# =========================================================
# HELPER: CALCULATE ASSESSMENT SCORE
# =========================================================

def calculate_assessment_score(criterion_scores):
    """
    Calculate the total score, maximum score and percentage
    from the AI criterion scores.
    """

    if not isinstance(criterion_scores, dict):
        criterion_scores = {}

    total_score = 0
    max_score = 0

    for criterion, details in criterion_scores.items():

        if not isinstance(details, dict):
            continue

        try:

            score = float(
                details.get(
                    'score',
                    0
                )
            )

        except (TypeError, ValueError):

            score = 0

        try:

            maximum = float(
                details.get(
                    'max_score',
                    0
                )
            )

        except (TypeError, ValueError):

            maximum = 0

        # Prevent negative scores
        if score < 0:
            score = 0

        # Prevent negative maximum marks
        if maximum < 0:
            maximum = 0

        # Prevent score from exceeding maximum
        if maximum > 0 and score > maximum:
            score = maximum

        details['score'] = score
        details['max_score'] = maximum

        total_score += score
        max_score += maximum

    # Calculate percentage
    if max_score > 0:

        percentage = (
            total_score / max_score
        ) * 100

    else:

        percentage = 0

    return (
        total_score,
        max_score,
        percentage
    )


# =========================================================
# HELPER: CALCULATE SUGGESTED GRADE
# =========================================================

def calculate_suggested_grade(percentage):
    """
    Convert the final percentage into the DWU
    suggested grading scale.

    0-49   = F
    50-55  = P
    56-65  = UP
    66-75  = C
    76-85  = D
    86-100 = HD
    """

    try:

        percentage = float(percentage)

    except (TypeError, ValueError):

        return ''

    # Keep percentage within valid range
    if percentage < 0:
        percentage = 0

    if percentage > 100:
        percentage = 100

    # DWU grading scale
    if percentage < 50:
        return 'F'

    elif percentage < 56:
        return 'P'

    elif percentage < 66:
        return 'UP'

    elif percentage < 76:
        return 'C'

    elif percentage < 86:
        return 'D'

    else:
        return 'HD'


# =========================================================
# STUDENT AI ASSESSMENT
# =========================================================

def student_ai_assessment(request, student_id):
    """
    Create and run an AI assessment for a specific student.

    This workflow is used when creating a new assignment
    together with the student's paper and marking guide.
    """

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    if request.method == 'POST':

        form = AIAssessmentForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            try:

                # =================================================
                # CREATE ASSIGNMENT
                # =================================================

                assignment = Assignment.objects.create(
                    student=student,
                    title=form.cleaned_data['title'],
                    document_type=form.cleaned_data[
                        'document_type'
                    ],
                )

                # =================================================
                # CREATE STUDENT SUBMISSION
                # =================================================

                submission = AssignmentSubmission.objects.create(
                    assignment=assignment,
                    file=form.cleaned_data[
                        'submission_file'
                    ],
                )

                # =================================================
                # EXTRACT STUDENT PAPER TEXT
                # =================================================

                submission.extracted_text = extract_text(
                    submission.file.path
                )

                submission.save()

                # =================================================
                # CREATE MARKING GUIDE
                # =================================================

                marking_guide = MarkingGuide.objects.create(
                    assignment=assignment,
                    title=form.cleaned_data[
                        'marking_guide_title'
                    ],
                    file=form.cleaned_data[
                        'marking_guide_file'
                    ],
                )

                # =================================================
                # EXTRACT MARKING GUIDE TEXT
                # =================================================

                marking_guide.extracted_text = extract_text(
                    marking_guide.file.path
                )

                marking_guide.save()

                # =================================================
                # CHECK STUDENT PAPER TEXT
                # =================================================

                if not submission.extracted_text:

                    raise ValueError(
                        'The student paper text could not be extracted.'
                    )

                # =================================================
                # CHECK MARKING GUIDE TEXT
                # =================================================

                if not marking_guide.extracted_text:

                    raise ValueError(
                        'The marking guide text could not be extracted.'
                    )

                # =================================================
                # RUN AI ASSESSMENT
                # =================================================

                result = assess_submission(
                    submission_text=submission.extracted_text,
                    marking_guide_text=(
                        marking_guide.extracted_text
                    ),
                    document_type=assignment.document_type
                )

                # =================================================
                # NORMALIZE AI RESPONSE
                # =================================================

                result = normalize_ai_result(
                    result
                )

                # =================================================
                # GET CRITERION SCORES
                # =================================================

                criterion_scores = result.get(
                    'criterion_scores',
                    {}
                )

                # =================================================
                # CALCULATE SCORE
                # =================================================

                (
                    total_score,
                    max_score,
                    percentage
                ) = calculate_assessment_score(
                    criterion_scores
                )

                # =================================================
                # CALCULATE SUGGESTED GRADE
                # =================================================

                grade = calculate_suggested_grade(
                    percentage
                )

                # =================================================
                # GET AI ANALYSIS
                # =================================================

                citation_analysis = result.get(
                    'citation_analysis',
                    {}
                )

                reference_analysis = result.get(
                    'reference_analysis',
                    {}
                )

                grammar_analysis = result.get(
                    'grammar_analysis',
                    {}
                )

                academic_writing_analysis = result.get(
                    'academic_writing_analysis',
                    {}
                )

                strengths = result.get(
                    'strengths',
                    []
                )

                weaknesses = result.get(
                    'weaknesses',
                    []
                )

                feedback = result.get(
                    'feedback',
                    ''
                )

                # =================================================
                # SAVE ASSESSMENT
                # =================================================

                assessment = Assessment.objects.create(
                    submission=submission,
                    ai_score=percentage,
                    ai_grade=grade,
                    criterion_scores=criterion_scores,
                    citation_analysis=citation_analysis,
                    reference_analysis=reference_analysis,
                    grammar_analysis=grammar_analysis,
                    academic_writing_analysis=(
                        academic_writing_analysis
                    ),
                    strengths=strengths,
                    weaknesses=weaknesses,
                    feedback=feedback,
                )

                # =================================================
                # SUCCESS
                # =================================================

                messages.success(
                    request,
                    'Assignment created successfully.'
                )

                return redirect(
                    'assignment_detail',
                    assignment_id=assignment.id
                )

            except AIAssessmentError as error:

                logger.warning(
                    'AI assessment failed '
                    'for student %s: %s',
                    student.id,
                    error
                )

                messages.error(
                    request,
                    str(error)
                )

            except ValueError as error:

                messages.error(
                    request,
                    str(error)
                )

            except Exception as error:

                logger.exception(
                    'Unexpected AI assessment failure '
                    'for student %s',
                    student.id
                )

                print(
                    '\n========== AI ASSESSMENT ERROR =========='
                )

                print(
                    f'Student ID: {student.id}'
                )

                print(
                    f'Error Type: {type(error).__name__}'
                )

                print(
                    f'Error: {error}'
                )

                print(
                    '==========================================\n'
                )

                messages.error(
                    request,
                    f'AI assessment error: {error}'
                )

    else:

        form = AIAssessmentForm()

    return render(
        request,
        'assessment/student_ai_assessment.html',
        {
            'student': student,
            'form': form,
        }
    )


# =========================================================
# ASSESSMENT DASHBOARD
# =========================================================

def assessment_dashboard(request):
    """
    Display all uploaded assignment submissions and their
    assessment status.
    """

    submissions = (
        AssignmentSubmission.objects
        .select_related(
            'assignment',
            'assignment__student'
        )
        .all()
    )

    assessment_data = []

    for submission in submissions:

        try:

            assessment = submission.assessment

        except Assessment.DoesNotExist:

            assessment = None

        assessment_data.append({
            'submission': submission,
            'assessment': assessment,
        })

    return render(
        request,
        'assessment/assessment_dashboard.html',
        {
            'assessment_data': assessment_data,
        }
    )


# =========================================================
# ASSESS ASSIGNMENT
# =========================================================

def assess_assignment(request, submission_id):
    """
    Run the AI assessment for an existing student submission.

    When called by the AI progress popup using AJAX/fetch,
    this function returns JSON.

    When opened normally in the browser, it redirects to
    the assessment result page.
    """

    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id
    )

    assignment = submission.assignment

    ajax_request = is_ajax_request(request)

    # =========================================================
    # CHECK MARKING GUIDE
    # =========================================================

    try:

        marking_guide = assignment.marking_guide

    except MarkingGuide.DoesNotExist:

        error_message = (
            'No marking guide has been uploaded '
            'for this assignment.'
        )

        if ajax_request:

            return JsonResponse(
                {
                    'success': False,
                    'error': error_message,
                },
                status=400
            )

        messages.error(
            request,
            error_message
        )

        return redirect(
            'assignment_detail',
            assignment_id=assignment.id
        )

    # =========================================================
    # CHECK SUBMISSION TEXT
    # =========================================================

    if not submission.extracted_text:

        error_message = (
            'The assignment text could not be extracted. '
            'Please upload a valid document and try again.'
        )

        if ajax_request:

            return JsonResponse(
                {
                    'success': False,
                    'error': error_message,
                },
                status=400
            )

        messages.error(
            request,
            error_message
        )

        return redirect(
            'assignment_detail',
            assignment_id=assignment.id
        )

    # =========================================================
    # CHECK MARKING GUIDE TEXT
    # =========================================================

    if not marking_guide.extracted_text:

        error_message = (
            'The marking guide text could not be extracted. '
            'Please upload a valid marking guide and try again.'
        )

        if ajax_request:

            return JsonResponse(
                {
                    'success': False,
                    'error': error_message,
                },
                status=400
            )

        messages.error(
            request,
            error_message
        )

        return redirect(
            'assignment_detail',
            assignment_id=assignment.id
        )

    # =========================================================
    # RUN AI ASSESSMENT
    # =========================================================

    try:

        result = assess_submission(
            submission_text=submission.extracted_text,
            marking_guide_text=(
                marking_guide.extracted_text
            ),
            document_type=assignment.document_type
        )

        # =====================================================
        # NORMALIZE AI RESPONSE
        # =====================================================

        result = normalize_ai_result(
            result
        )

        # =====================================================
        # GET CRITERION SCORES
        # =====================================================

        criterion_scores = result.get(
            'criterion_scores',
            {}
        )

        # =====================================================
        # CALCULATE SCORE
        # =====================================================

        (
            total_score,
            max_score,
            percentage
        ) = calculate_assessment_score(
            criterion_scores
        )

        # =====================================================
        # CALCULATE SUGGESTED GRADE
        # =====================================================

        grade = calculate_suggested_grade(
            percentage
        )

        # =====================================================
        # GET AI ANALYSIS
        # =====================================================

        citation_analysis = result.get(
            'citation_analysis',
            {}
        )

        reference_analysis = result.get(
            'reference_analysis',
            {}
        )

        grammar_analysis = result.get(
            'grammar_analysis',
            {}
        )

        academic_writing_analysis = result.get(
            'academic_writing_analysis',
            {}
        )

        strengths = result.get(
            'strengths',
            []
        )

        weaknesses = result.get(
            'weaknesses',
            []
        )

        feedback = result.get(
            'feedback',
            ''
        )

        # =====================================================
        # SAVE OR UPDATE ASSESSMENT
        # =====================================================

        assessment, created = (
            Assessment.objects.update_or_create(
                submission=submission,
                defaults={
                    'ai_score': percentage,
                    'ai_grade': grade,
                    'criterion_scores': criterion_scores,
                    'citation_analysis': citation_analysis,
                    'reference_analysis': reference_analysis,
                    'grammar_analysis': grammar_analysis,
                    'academic_writing_analysis': (
                        academic_writing_analysis
                    ),
                    'strengths': strengths,
                    'weaknesses': weaknesses,
                    'feedback': feedback,
                }
            )
        )

        # =====================================================
        # AJAX SUCCESS RESPONSE
        # =====================================================

        if ajax_request:

            return JsonResponse(
                {
                    'success': True,

                    'assessment_id':
                        assessment.id,

                    'score':
                        round(
                            total_score,
                            2
                        ),

                    'max_score':
                        round(
                            max_score,
                            2
                        ),

                    'percentage':
                        round(
                            percentage,
                            2
                        ),

                    'grade':
                        grade,

                    'result_url':
                        (
                            f'/assessment/result/'
                            f'{assessment.id}/'
                        ),
                }
            )

        # =====================================================
        # NORMAL BROWSER SUCCESS
        # =====================================================

        return redirect(
            'assessment_result',
            assessment_id=assessment.id
        )

    # =========================================================
    # AI SERVICE ERROR
    # =========================================================

    except AIAssessmentError as error:

        logger.warning(
            'AI assessment failed '
            'for submission %s: %s',
            submission.id,
            error
        )

        error_message = str(error)

        if ajax_request:

            return JsonResponse(
                {
                    'success': False,
                    'error': error_message,
                },
                status=503
            )

        messages.error(
            request,
            error_message
        )

        return redirect(
            'assignment_detail',
            assignment_id=assignment.id
        )

    # =========================================================
    # INVALID AI RESPONSE / OTHER ERROR
    # =========================================================

    except Exception as error:

        logger.exception(
            'Unexpected AI assessment failure '
            'for submission %s',
            submission.id
        )

        print(
            '\n========== AI ASSESSMENT ERROR =========='
        )

        print(
            f'Submission ID: {submission.id}'
        )

        print(
            f'Assignment: {assignment.title}'
        )

        print(
            f'Error Type: {type(error).__name__}'
        )

        print(
            f'Error: {error}'
        )

        print(
            '==========================================\n'
        )

        error_message = (
            f'AI assessment error: {error}'
        )

        if ajax_request:

            return JsonResponse(
                {
                    'success': False,
                    'error': error_message,
                },
                status=500
            )

        messages.error(
            request,
            error_message
        )

        return redirect(
            'assignment_detail',
            assignment_id=assignment.id
        )


# =========================================================
# ASSESSMENT RESULT
# =========================================================

def assessment_result(request, assessment_id):
    """
    Display the complete AI assessment result.
    """

    assessment = get_object_or_404(
        Assessment,
        id=assessment_id
    )

    total_score = 0
    max_score = 0

    criterion_scores = (
        assessment.criterion_scores or {}
    )

    if isinstance(
        criterion_scores,
        dict
    ):

        for criterion, details in criterion_scores.items():

            if not isinstance(
                details,
                dict
            ):
                continue

            try:

                score = float(
                    details.get(
                        'score',
                        0
                    )
                )

            except (TypeError, ValueError):

                score = 0

            try:

                maximum = float(
                    details.get(
                        'max_score',
                        0
                    )
                )

            except (TypeError, ValueError):

                maximum = 0

            if score < 0:
                score = 0

            if maximum < 0:
                maximum = 0

            if maximum > 0 and score > maximum:
                score = maximum

            total_score += score
            max_score += maximum

    # =========================================================
    # CALCULATE PERCENTAGE
    # =========================================================

    if max_score > 0:

        percentage = (
            total_score / max_score
        ) * 100

    else:

        percentage = 0

    # =========================================================
    # CALCULATE SUGGESTED GRADE
    # =========================================================

    suggested_grade = calculate_suggested_grade(
        percentage
    )

    # =========================================================
    # RETURN RESULT PAGE
    # =========================================================

    return render(
        request,
        'assessment/assessment_result.html',
        {
            'assessment': assessment,
            'total_score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'suggested_grade': suggested_grade,
        }
    )
