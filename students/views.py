from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db import transaction

from lecturers.models import LecturerProfile

from assignments.models import Assignment
from assessment.models import Assessment

from assignments.forms import AssignmentSubmissionForm

from .forms import (
    StudentProfileForm,
    StudentSelfProfileForm,
    StudentEnrollmentForm,
)

from .models import (
    StudentProfile,
    Enrollment,
    GradebookEntry,
    CourseUnit,
)


# =========================================================
# LECTURER ACCESS
# =========================================================

def lecturer_only(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:

            lecturer_profile = request.user.lecturer_profile

        except LecturerProfile.DoesNotExist:

            messages.error(
                request,
                "You do not have lecturer access."
            )

            return redirect(
                "student_login"
            )

        if not lecturer_profile:

            messages.error(
                request,
                "You do not have lecturer access."
            )

            return redirect(
                "student_login"
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# STUDENT LOGIN
# =========================================================

def student_login(request):

    if request.user.is_authenticated:

        try:

            student = request.user.student_profile

            if student.must_change_password:

                return redirect(
                    "student_change_password"
                )

            return redirect(
                "student_dashboard"
            )

        except StudentProfile.DoesNotExist:

            pass

    if request.method == "POST":

        student_id = request.POST.get(
            "student_id",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not student_id or not password:

            messages.error(
                request,
                "Please enter your Student ID and password."
            )

            return render(
                request,
                "students/student_login.html"
            )

        try:

            student = StudentProfile.objects.get(
                student_id=student_id
            )

        except StudentProfile.DoesNotExist:

            messages.error(
                request,
                "Invalid Student ID or password."
            )

            return render(
                request,
                "students/student_login.html"
            )

        user = authenticate(
            request,
            username=student.user.username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            if student.must_change_password:

                return redirect(
                    "student_change_password"
                )

            return redirect(
                "student_dashboard"
            )

        messages.error(
            request,
            "Invalid Student ID or password."
        )

    return render(
        request,
        "students/student_login.html"
    )


# =========================================================
# STUDENT CHANGE PASSWORD
# =========================================================

@login_required
def student_change_password(request):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    if request.method == "POST":

        new_password = request.POST.get(
            "new_password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not new_password or not confirm_password:

            messages.error(
                request,
                "Please enter and confirm your new password."
            )

            return render(
                request,
                "students/student_change_password.html",
                {
                    "student": student,
                }
            )

        if new_password != confirm_password:

            messages.error(
                request,
                "The passwords do not match."
            )

            return render(
                request,
                "students/student_change_password.html",
                {
                    "student": student,
                }
            )

        if len(new_password) < 8:

            messages.error(
                request,
                "Password must be at least 8 characters long."
            )

            return render(
                request,
                "students/student_change_password.html",
                {
                    "student": student,
                }
            )

        request.user.set_password(
            new_password
        )

        request.user.save()

        student.must_change_password = False

        student.save(
            update_fields=[
                "must_change_password"
            ]
        )

        user = authenticate(
            request,
            username=request.user.username,
            password=new_password
        )

        if user is not None:

            login(
                request,
                user
            )

        messages.success(
            request,
            "Your password has been changed successfully."
        )

        return redirect(
            "student_dashboard"
        )

    return render(
        request,
        "students/student_change_password.html",
        {
            "student": student,
        }
    )


# =========================================================
# STUDENT LOGOUT
# =========================================================

@login_required
def student_logout(request):

    logout(request)

    return redirect(
        "student_login"
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@login_required
def student_dashboard(request):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    enrollments = (
        Enrollment.objects
        .filter(
            student=student
        )
        .select_related(
            "course_unit"
        )
        .order_by(
            "course_unit__code"
        )
    )

    selected_unit = None

    unit_id = request.GET.get(
        "unit"
    )

    if unit_id:

        selected_unit = get_object_or_404(
            CourseUnit,
            id=unit_id
        )

        is_enrolled = enrollments.filter(
            course_unit=selected_unit
        ).exists()

        if not is_enrolled:

            messages.error(
                request,
                "You are not enrolled in this course unit."
            )

            selected_unit = None

    assignments = Assignment.objects.none()

    if selected_unit:

        assignments = (
            Assignment.objects
            .filter(
                student=student,
                course_unit=selected_unit,
                allow_student_access=True
            )
            .order_by(
                "-due_date",
                "-id"
            )
        )

    return render(
        request,
        "students/dashboard.html",
        {
            "student": student,
            "enrollments": enrollments,
            "selected_unit": selected_unit,
            "assignments": assignments,
        }
    )


# =========================================================
# STUDENT GRADEBOOK PAGE
# =========================================================

@login_required
def student_gradebook_page(request):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    enrollments = (
        Enrollment.objects
        .filter(
            student=student
        )
        .select_related(
            "course_unit"
        )
        .order_by(
            "course_unit__code"
        )
    )

    selected_unit = None

    unit_id = request.GET.get(
        "unit"
    )

    if unit_id:

        selected_unit = get_object_or_404(
            CourseUnit,
            id=unit_id
        )

        is_enrolled = enrollments.filter(
            course_unit=selected_unit
        ).exists()

        if not is_enrolled:

            messages.error(
                request,
                "You are not enrolled in this course unit."
            )

            return redirect(
                "student_gradebook_page"
            )

    if not selected_unit:

        return render(
            request,
            "students/student_portal_gradebook.html",
            {
                "student": student,
                "enrollments": enrollments,
                "selected_unit": None,
                "gradebook_entries": [],
                "visible_final_grade": "",
                "final_grade_released": False,
                "total_score": Decimal("0"),
                "max_score": Decimal("0"),
            }
        )

    visible_entries = (
        GradebookEntry.objects
        .filter(
            student=student,
            course_unit=selected_unit,
            is_visible=True
        )
        .exclude(
            assessment_type=""
        )
        .order_by(
            "created_at"
        )
    )

    final_grade_entry = (
        visible_entries
        .exclude(
            final_grade=""
        )
        .exclude(
            final_grade__isnull=True
        )
        .order_by(
            "-updated_at"
        )
        .first()
    )

    visible_final_grade = ""

    final_grade_released = False

    if final_grade_entry:

        visible_final_grade = (
            final_grade_entry.final_grade
        )

        final_grade_released = True

    total_score = Decimal("0")

    max_score = Decimal("0")

    for entry in visible_entries:

        if entry.mark is None:

            continue

        try:

            mark = Decimal(
                str(entry.mark)
            )

            total_score += mark

            max_score += Decimal("100")

        except (
            InvalidOperation,
            TypeError,
            ValueError
        ):

            continue

    return render(
        request,
        "students/student_portal_gradebook.html",
        {
            "student": student,
            "enrollments": enrollments,
            "selected_unit": selected_unit,
            "gradebook_entries": visible_entries,
            "visible_final_grade": visible_final_grade,
            "final_grade_released": final_grade_released,
            "total_score": total_score,
            "max_score": max_score,
        }
    )


# =========================================================
# STUDENT LIST
# =========================================================

@lecturer_only
def student_list(request):

    lecturer_profile = None

    if not request.user.is_superuser:

        lecturer_profile = get_object_or_404(
            LecturerProfile,
            user=request.user
        )

    if request.user.is_superuser:

        students = (
            StudentProfile.objects
            .select_related(
                "user"
            )
            .order_by(
                "full_name"
            )
        )

    else:

        students = (
            StudentProfile.objects
            .filter(
                lecturer=lecturer_profile
            )
            .select_related(
                "user"
            )
            .order_by(
                "full_name"
            )
        )

    student_created = request.session.pop(
        "student_created",
        None
    )

    return render(
        request,
        "students/student_list.html",
        {
            "students": students,
            "student_created": student_created,
        }
    )


# =========================================================
# CREATE STUDENT
# =========================================================

@lecturer_only
def student_create(request):

    if request.method == "POST":

        form = StudentProfileForm(
            request.POST
        )

        if form.is_valid():

            student = form.save(
                commit=False
            )

            if not request.user.is_superuser:

                student.lecturer = get_object_or_404(
                    LecturerProfile,
                    user=request.user
                )

            default_password = (
                f"{student.student_id}@DWU"
            )

            user = User.objects.create_user(
                username=student.student_id,
                password=default_password,
                first_name=student.full_name
            )

            student.user = user

            student.must_change_password = True

            student.save()

            request.session["student_created"] = {

                "student_id": student.student_id,

                "full_name": student.full_name,

                "default_password": default_password,

            }

            return redirect(
                "student_list"
            )

    else:

        form = StudentProfileForm()

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "title": "Create Student",
        }
    )


# =========================================================
# DELETE STUDENT
# =========================================================

@lecturer_only
def student_delete(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    if not request.user.is_superuser:

        lecturer = get_object_or_404(
            LecturerProfile,
            user=request.user
        )

        if student.lecturer != lecturer:

            messages.error(
                request,
                "You are not allowed to delete this student."
            )

            return redirect(
                "student_list"
            )

    if request.method == "POST":

        student.delete()

        return redirect(
            "student_list"
        )

    return render(
        request,
        "students/student_confirm_delete.html",
        {
            "student": student
        }
    )


# =========================================================
# STUDENT DETAIL
# =========================================================

@lecturer_only
def student_detail(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    if not request.user.is_superuser:

        lecturer_profile = get_object_or_404(
            LecturerProfile,
            user=request.user
        )

        if student.lecturer != lecturer_profile:

            messages.error(
                request,
                "You do not have permission to view this student."
            )

            return redirect(
                "student_list"
            )

    enrollments = (
        Enrollment.objects
        .filter(
            student=student
        )
        .select_related(
            "course_unit"
        )
        .order_by(
            "course_unit__code"
        )
    )

    return render(
        request,
        "students/student_detail.html",
        {
            "student": student,
            "enrollments": enrollments,
        }
    )


# =========================================================
# ENROLL STUDENT
# =========================================================

@lecturer_only
def student_enroll(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    if not request.user.is_superuser:

        lecturer_profile = get_object_or_404(
            LecturerProfile,
            user=request.user
        )

        if student.lecturer != lecturer_profile:

            messages.error(
                request,
                "You do not have permission to enroll this student."
            )

            return redirect(
                "student_list"
            )

    if request.method == "POST":

        form = StudentEnrollmentForm(
            request.POST
        )

        if form.is_valid():

            course_unit = form.cleaned_data[
                "course_unit"
            ]

            already_enrolled = Enrollment.objects.filter(
                student=student,
                course_unit=course_unit
            ).exists()

            if already_enrolled:

                messages.warning(
                    request,
                    f"{student.full_name} is already enrolled "
                    f"in {course_unit.code}."
                )

                return redirect(
                    "student_detail",
                    student_id=student.id
                )

            Enrollment.objects.create(
                student=student,
                course_unit=course_unit
            )

            return redirect(
                "student_detail",
                student_id=student.id
            )

    else:

        form = StudentEnrollmentForm()

    return render(
        request,
        "students/student_enroll.html",
        {
            "form": form,
            "student": student,
        }
    )


# =========================================================
# LECTURER GRADEBOOK
# =========================================================

@lecturer_only
def student_gradebook(request, student_id):

    student = get_object_or_404(
        StudentProfile,
        id=student_id
    )

    # =====================================================
    # VERIFY LECTURER ACCESS
    # =====================================================

    if not request.user.is_superuser:

        lecturer_profile = get_object_or_404(
            LecturerProfile,
            user=request.user
        )

        if student.lecturer != lecturer_profile:

            messages.error(
                request,
                "You do not have permission to access this gradebook."
            )

            return redirect(
                "student_list"
            )

    # =====================================================
    # COURSE UNITS
    # =====================================================

    unit_id = request.GET.get(
        "unit"
    )

    course_units = (
        CourseUnit.objects
        .filter(
            enrollments__student=student
        )
        .distinct()
        .order_by(
            "code"
        )
    )

    selected_unit = None

    if unit_id:

        selected_unit = get_object_or_404(
            CourseUnit,
            id=unit_id
        )

        is_enrolled = Enrollment.objects.filter(
            student=student,
            course_unit=selected_unit
        ).exists()

        if not is_enrolled:

            messages.error(
                request,
                "This student is not enrolled in the selected course unit."
            )

            return redirect(
                "student_gradebook",
                student_id=student.id
            )

    # =====================================================
    # POST - SAVE GRADEBOOK
    # =====================================================

    if request.method == "POST":

        selected_unit_id = request.POST.get(
            "course_unit",
            ""
        ).strip()

        if not selected_unit_id:

            messages.error(
                request,
                "Please select a course unit."
            )

            return redirect(
                "student_gradebook",
                student_id=student.id
            )

        selected_unit = get_object_or_404(
            CourseUnit,
            id=selected_unit_id
        )

        # =================================================
        # VERIFY STUDENT ENROLLMENT
        # =================================================

        is_enrolled = Enrollment.objects.filter(
            student=student,
            course_unit=selected_unit
        ).exists()

        if not is_enrolled:

            messages.error(
                request,
                "This student is not enrolled in the selected course unit."
            )

            return redirect(
                "student_gradebook",
                student_id=student.id
            )

        # =================================================
        # ROW COUNT
        # =================================================

        try:

            row_count = int(
                request.POST.get(
                    "row_count",
                    "0"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            row_count = 0

        submitted_entry_ids = []

        rows = []

        # =================================================
        # READ ALL ROWS
        # =================================================

        for index in range(
            1,
            row_count + 1
        ):

            # =============================================
            # ENTRY ID
            # =============================================

            entry_id = (
                request.POST.get(
                    f"entry_id_{index}",
                    ""
                )
                .strip()
            )

            # =============================================
            # ASSESSMENT TYPE
            # =============================================

            assessment_type = (
                request.POST.get(
                    f"assessment_type_{index}",
                    ""
                )
                .strip()
            )

            # =============================================
            # ASSESSMENT DETAILS
            # =============================================

            assessment_details = (
                request.POST.get(
                    f"assessment_details_{index}",
                    ""
                )
                .strip()
            )

            # =============================================
            # MARK
            # =============================================

            mark_value = (
                request.POST.get(
                    f"mark_{index}",
                    ""
                )
                .strip()
            )

            # =============================================
            # FINAL GRADE
            #
            # IMPORTANT:
            # Each row has its own final_grade field.
            #
            # Example:
            #
            # final_grade_1 = C
            # final_grade_2 = F
            # final_grade_3 = B
            # =============================================

            final_grade = (
                request.POST.get(
                    f"final_grade_{index}",
                    ""
                )
                .strip()
            )

            # =============================================
            # VISIBILITY
            # =============================================

            visibility_value = (
                request.POST.get(
                    f"visibility_{index}",
                    "0"
                )
                .strip()
                .lower()
            )

            is_visible = visibility_value in {
                "1",
                "true",
                "on",
                "yes",
            }

            # =============================================
            # SKIP COMPLETELY EMPTY ROWS
            # =============================================

            if (
                not entry_id
                and not assessment_type
                and not assessment_details
                and not mark_value
                and not final_grade
            ):

                continue

            # =============================================
            # STORE ROW DATA
            # =============================================

            rows.append(
                {
                    "entry_id": entry_id,

                    "assessment_type": assessment_type,

                    "assessment_details": assessment_details,

                    "mark_value": mark_value,

                    "final_grade": final_grade,

                    "is_visible": is_visible,
                }
            )

        # =====================================================
        # SAVE GRADEBOOK IN ONE DATABASE TRANSACTION
        # =====================================================

        with transaction.atomic():

            # =================================================
            # SAVE EACH ROW
            # =================================================

            for row_index, row in enumerate(
                rows,
                start=1
            ):

                entry_id = row["entry_id"]

                # =============================================
                # EXISTING ENTRY
                # =============================================

                if entry_id:

                    entry = get_object_or_404(
                        GradebookEntry,
                        id=entry_id,
                        student=student,
                        course_unit=selected_unit
                    )

                # =============================================
                # NEW ENTRY
                # =============================================

                else:

                    entry = GradebookEntry(
                        student=student,
                        course_unit=selected_unit
                    )

                # =============================================
                # ASSESSMENT TYPE
                # =============================================

                assessment_type = (
                    row["assessment_type"]
                )

                if not assessment_type:

                    assessment_type = (
                        f"Assessment {row_index}"
                    )

                entry.assessment_type = (
                    assessment_type
                )

                # =============================================
                # ASSESSMENT DETAILS
                # =============================================

                entry.assessment_details = (
                    row["assessment_details"]
                )

                # =============================================
                # MARK
                # =============================================

                mark_value = row["mark_value"]

                if mark_value:

                    try:

                        mark = Decimal(
                            mark_value
                        )

                        if mark < 0 or mark > 100:

                            messages.error(
                                request,
                                "Marks must be between 0 and 100."
                            )

                            return redirect(
                                "student_gradebook",
                                student_id=student.id
                            )

                        entry.mark = mark

                    except (
                        InvalidOperation,
                        TypeError,
                        ValueError
                    ):

                        messages.error(
                            request,
                            "Please enter a valid mark."
                        )

                        return redirect(
                            "student_gradebook",
                            student_id=student.id
                        )

                else:

                    entry.mark = None

                # =============================================
                # VISIBILITY
                # =============================================

                entry.is_visible = bool(
                    row["is_visible"]
                )

                # =============================================
                # FINAL GRADE
                #
                # IMPORTANT:
                #
                # Save the final grade for EVERY row.
                #
                # This fixes the previous problem where only
                # the newly-created assessment received the
                # submitted final grade.
                #
                # Example:
                #
                # Assessment 1 -> C
                # Assessment 2 -> F
                #
                # Both values are saved independently.
                # =============================================

                entry.final_grade = (
                    row["final_grade"]
                )

                # =============================================
                # SAVE ENTRY
                #
                # Normal save() works for both:
                #
                # Existing entry -> UPDATE
                # New entry      -> INSERT
                # =============================================

                entry.save()

                submitted_entry_ids.append(
                    entry.id
                )

            # =================================================
            # DELETE OLD ROWS THAT WERE REMOVED
            # =================================================

            old_entries = GradebookEntry.objects.filter(
                student=student,
                course_unit=selected_unit
            )

            if submitted_entry_ids:

                old_entries.exclude(
                    id__in=submitted_entry_ids
                ).delete()

            else:

                old_entries.delete()

        # =====================================================
        # RETURN TO SAME GRADEBOOK
        # =====================================================

        gradebook_url = reverse(
            "student_gradebook",
            kwargs={
                "student_id": student.id
            }
        )

        return redirect(
            f"{gradebook_url}?unit={selected_unit.id}"
        )

    # =====================================================
    # GET - LOAD EXISTING GRADEBOOK
    # =====================================================

    gradebook_entries = []

    if selected_unit:

        gradebook_entries = (
            GradebookEntry.objects
            .filter(
                student=student,
                course_unit=selected_unit
            )
            .order_by(
                "created_at"
            )
        )

    # =====================================================
    # RETURN LECTURER GRADEBOOK
    # =====================================================

    return render(
        request,
        "students/student_gradebook.html",
        {
            "student": student,

            "course_units": course_units,

            "selected_unit": selected_unit,

            "gradebook_entries": gradebook_entries,
        }
    )


# =========================================================
# STUDENT SUBMIT / VIEW ASSIGNMENT
# =========================================================

@login_required
def student_submit_assignment(request, assignment_id):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        student=student,
        allow_student_access=True
    )

    # =====================================================
    # GET LATEST SUBMISSION
    # =====================================================

    submission = (
        assignment.submissions
        .order_by(
            "-submitted_at"
        )
        .first()
    )

    # =====================================================
    # SUBMISSION FORM
    # =====================================================

    if request.method == "POST":

        form = AssignmentSubmissionForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            new_submission = form.save(
                commit=False
            )

            new_submission.assignment = assignment

            new_submission.save()

            return redirect(
                "student_submit_assignment",
                assignment_id=assignment.id
            )

    else:

        form = AssignmentSubmissionForm()

    # =====================================================
    # GRADING STATUS
    # =====================================================

    grading_status = "Not graded"

    if submission:

        grading_status = "Yet to be graded"

        # =================================================
        # CHECK WHETHER LECTURER HAS RELEASED THE GRADE
        # =================================================

        released_grade = (
            GradebookEntry.objects
            .filter(
                student=student,
                course_unit=assignment.course_unit,
                is_visible=True
            )
            .exclude(
                mark__isnull=True
            )
            .exclude(
                final_grade=""
            )
            .exclude(
                final_grade__isnull=True
            )
        )

        # =================================================
        # MATCH ASSIGNMENT WITH GRADEBOOK ENTRY
        # =================================================

        assignment_grade = released_grade.filter(
            assessment_details__icontains=assignment.title
        ).first()

        if assignment_grade:

            grading_status = "Graded"

    # =====================================================
    # RETURN PAGE
    # =====================================================

    return render(
        request,
        "students/student_submit_assignment.html",
        {
            "student": student,

            "assignment": assignment,

            "submission": submission,

            "form": form,

            "grading_status": grading_status,
        }
    )


# =========================================================
# STUDENT MY PROFILE
# =========================================================

@login_required
def student_profile(request):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    if request.method == "POST":

        form = StudentSelfProfileForm(
            request.POST,
            request.FILES,
            instance=student
        )

        if form.is_valid():

            student = form.save()

            request.user.first_name = (
                student.full_name
            )

            request.user.save(
                update_fields=[
                    "first_name"
                ]
            )

            messages.success(
                request,
                "Your profile has been updated successfully."
            )

            return redirect(
                "student_profile"
            )

    else:

        form = StudentSelfProfileForm(
            instance=student
        )

    return render(
        request,
        "students/student_profile.html",
        {
            "student": student,

            "form": form,
        }
    )


# =========================================================
# STUDENT ACCOUNT DETAILS
# =========================================================

@login_required
def student_account_details(request):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )

    return render(
        request,
        "students/student_account_details.html",
        {
            "student": student,
        }
    )