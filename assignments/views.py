
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from students.models import StudentProfile
from assessment.models import Assessment

from .forms import (
    AssignmentForm,
    AssignmentSubmissionForm,
    MarkingGuideForm,
)

from .models import (
    Assignment,
    AssignmentSubmission,
    MarkingGuide,
)

from .services.document_parser import extract_text


def lecturer_only(request):

    return (
        request.user.is_authenticated
        and (
            request.user.is_superuser
            or hasattr(request.user, 'lecturer_profile')
        )
    )


@login_required
def create_assignment(request, student_id):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    if request.method == 'POST':

        form = AssignmentForm(
            request.POST,
            student=student
        )

        if form.is_valid():

            assignment = form.save(commit=False)

            assignment.student = student

            assignment.save()

            messages.success(
                request,
                'Assignment created successfully.'
            )

            # Return to the student's assignment table
            # instead of opening the assignment detail page.
            return redirect(
                'student_assignments',
                student_id=student.id
            )

    else:

        form = AssignmentForm(
            student=student
        )

    return render(
        request,
        'assignments/create_assignment.html',
        {
            'form': form,
            'student': student,
        }
    )


@login_required
def student_assignments(request, student_id):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    assignments = Assignment.objects.filter(
        student=student
    ).order_by('-created_at')

    # Get the latest submission and its assessment
    # for each assignment.
    for assignment in assignments:

        try:
            assignment.latest_submission = (
                assignment.submissions.latest('submitted_at')
            )

        except AssignmentSubmission.DoesNotExist:

            assignment.latest_submission = None

        assignment.assessment = None

        if assignment.latest_submission:

            try:

                assignment.assessment = (
                    assignment.latest_submission.assessment
                )

            except Assessment.DoesNotExist:

                assignment.assessment = None

    return render(
        request,
        'assignments/student_assignments.html',
        {
            'student': student,
            'assignments': assignments,
        }
    )


@login_required
def assignment_detail(request, assignment_id):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id
    )

    try:

        submission = assignment.submissions.latest(
            'submitted_at'
        )

    except AssignmentSubmission.DoesNotExist:

        submission = None

    try:

        marking_guide = assignment.marking_guide

    except MarkingGuide.DoesNotExist:

        marking_guide = None

    assessment = None

    if submission:

        try:

            assessment = submission.assessment

        except Exception:

            assessment = None

    return render(
        request,
        'assignments/assignment_detail.html',
        {
            'assignment': assignment,
            'submission': submission,
            'marking_guide': marking_guide,
            'assessment': assessment,
        }
    )


@login_required
def upload_assignment_submission(
    request,
    assignment_id
):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id
    )

    if request.method == 'POST':

        form = AssignmentSubmissionForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            submission = form.save(
                commit=False
            )

            submission.assignment = assignment

            submission.save()

            try:

                submission.extracted_text = extract_text(
                    submission.file.path
                )

                submission.save()

                messages.success(
                    request,
                    'Assignment submission uploaded and text extracted successfully.'
                )

                return redirect(
                    'assignment_detail',
                    assignment_id=assignment.id
                )

            except ValueError as error:

                submission.delete()

                form.add_error(
                    'file',
                    str(error)
                )

    else:

        form = AssignmentSubmissionForm()

    return render(
        request,
        'assignments/upload_assignment_submission.html',
        {
            'form': form,
            'assignment': assignment,
        }
    )


@login_required
def upload_assignment_marking_guide(
    request,
    assignment_id
):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id
    )

    if request.method == 'POST':

        form = MarkingGuideForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # Because MarkingGuide has a OneToOneField,
            # an assignment can only have one marking guide.
            try:

                marking_guide = assignment.marking_guide

                marking_guide.title = form.cleaned_data[
                    'title'
                ]

                marking_guide.file = form.cleaned_data[
                    'file'
                ]

            except MarkingGuide.DoesNotExist:

                marking_guide = form.save(
                    commit=False
                )

                marking_guide.assignment = assignment

            marking_guide.save()

            try:

                marking_guide.extracted_text = extract_text(
                    marking_guide.file.path
                )

                marking_guide.save()

                messages.success(
                    request,
                    'Marking guide uploaded and text extracted successfully.'
                )

                return redirect(
                    'assignment_detail',
                    assignment_id=assignment.id
                )

            except ValueError as error:

                form.add_error(
                    'file',
                    str(error)
                )

    else:

        form = MarkingGuideForm()

    return render(
        request,
        'assignments/upload_assignment_marking_guide.html',
        {
            'form': form,
            'assignment': assignment,
        }
    )


@login_required
def upload_submission(request):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    messages.info(
        request,
        'Please select a student and assignment before uploading a submission.'
    )

    return redirect('assessment_dashboard')


def marking_guide_success(request):

    return render(
        request,
        'assignments/marking_guide_success.html'
    )


@login_required
def delete_assignment(request, assignment_id):

    if not lecturer_only(request):
        return redirect('lecturer_login')

    if request.method != 'POST':

        messages.error(
            request,
            'Invalid request. Assignments can only be deleted using the delete button.'
        )

        return redirect('assessment_dashboard')

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id
    )

    assignment_title = assignment.title

    student_id = assignment.student.id

    assignment.delete()

    messages.success(
        request,
        f'Assignment "{assignment_title}" was deleted successfully.'
    )

    return redirect(
        'student_detail',
        student_id=student_id
    )
