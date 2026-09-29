from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from lecturers.models import LecturerProfile

from assignments.models import Assignment
from assignments.forms import AssignmentSubmissionForm

from .forms import (
    StudentProfileForm,
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
            return redirect("student_login")

        if not lecturer_profile:
            messages.error(
                request,
                "You do not have lecturer access."
            )
            return redirect("student_login")

        return view_func(request, *args, **kwargs)

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


        # Log the student back in because changing the
        # password invalidates the existing session.

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

    # =====================================================
    # GET STUDENT PROFILE
    # =====================================================

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )


    # =====================================================
    # GET ENROLLED COURSE UNITS
    # =====================================================

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


    # =====================================================
    # GET SELECTED COURSE UNIT
    # =====================================================

    selected_unit = None

    unit_id = request.GET.get(
        "unit"
    )


    if unit_id:

        selected_unit = get_object_or_404(
            CourseUnit,
            id=unit_id
        )


        # Make sure the student is enrolled
        # in the selected course unit.

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


    # =====================================================
    # NO COURSE UNIT SELECTED
    # =====================================================

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


    # =====================================================
    # GET ALL GRADEBOOK ENTRIES
    # =====================================================

    all_entries = (
        GradebookEntry.objects
        .filter(
            student=student,
            course_unit=selected_unit
        )
        .exclude(
            assessment_type=""
        )
        .order_by(
            "created_at"
        )
    )


    # =====================================================
    # FIND FINAL GRADE
    #
    # The final grade is stored independently from
    # individual assessment visibility.
    # =====================================================

    final_grade_entry = (
        all_entries
        .exclude(
            final_grade=""
        )
        .exclude(
            final_grade__isnull=True
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


    # =====================================================
    # ONLY SHOW ASSESSMENTS RELEASED TO STUDENT
    # =====================================================

    visible_entries = (
        all_entries
        .filter(
            is_visible=True
        )
    )


    gradebook_entries = visible_entries


    # =====================================================
    # CALCULATE SCORE
    #
    # Each GradebookEntry mark is stored out of 100.
    #
    # Example:
    #
    # Tutorial 1       85
    # Assignment 1    78
    # Mid-Sem Test    72
    #
    # Total = 235
    # Maximum = 300
    #
    # Student sees:
    #
    # Score     235 / 300
    # =====================================================

    total_score = Decimal("0")

    max_score = Decimal("0")


    for entry in gradebook_entries:

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


    # =====================================================
    # RENDER STUDENT GRADEBOOK
    # =====================================================

    return render(
        request,
        "students/student_portal_gradebook.html",
        {
            "student": student,

            "enrollments": enrollments,

            "selected_unit": selected_unit,

            "gradebook_entries": gradebook_entries,

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


    return render(
        request,
        "students/student_list.html",
        {
            "students": students,
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


            # Assign the logged-in lecturer
            # unless this is the administrator.

            if not request.user.is_superuser:

                student.lecturer = get_object_or_404(
                    LecturerProfile,
                    user=request.user
                )


            student.save()


            messages.success(
                     request,
                     f"Student profile created successfully. "
                     f"Default Password: {student.student_id}@DWU"
                 )


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

@lecturer_only
def student_delete(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)

    # Only allow the lecturer who owns the student to delete them
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
            return redirect("student_list")

    if request.method == "POST":
        student_name = student.full_name
        student.delete()

        messages.success(
            request,
            f"Student profile for {student_name} was deleted successfully."
        )

        return redirect("student_list")

    return render(
        request,
        "students/student_confirm_delete.html",
        {"student": student}
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


    # Lecturer can only access their own students.

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
                "You do not have permission to enroll this student."
            )

            return redirect(
                "student_list"
            )


    # =====================================================
    # ENROLLMENT FORM
    # =====================================================

    if request.method == "POST":

        form = StudentEnrollmentForm(
            request.POST
        )


        if form.is_valid():

            # Get the course unit selected by the lecturer.

            course_unit = form.cleaned_data[
                "course_unit"
            ]


            # =================================================
            # CHECK IF ALREADY ENROLLED
            # =================================================

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


            # =================================================
            # CREATE ENROLLMENT
            # =================================================

            Enrollment.objects.create(
                student=student,
                course_unit=course_unit
            )


            messages.success(
                request,
                f"{student.full_name} has been enrolled "
                f"in {course_unit.code} successfully."
            )


            # Return to the lecturer's Student Profile page.

            return redirect(
                "student_detail",
                student_id=student.id
            )


    else:

        form = StudentEnrollmentForm()


    # =====================================================
    # DISPLAY ENROLLMENT PAGE
    # =====================================================

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
    # COURSE UNIT
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
            "course_unit"
        )


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


        # Make sure student is enrolled.

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
        # FINAL GRADE
        # =================================================

        final_grade = (
            request.POST.get(
                "final_grade",
                ""
            )
            .strip()
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

        except (TypeError, ValueError):

            row_count = 0


        submitted_entry_ids = []


        # =================================================
        # READ ALL ROWS FIRST
        #
        # This prevents saved rows from being accidentally
        # deleted when new rows are added.
        # =================================================

        rows = []


        for index in range(row_count):

            entry_id = (
                request.POST.get(
                    f"entry_id_{index}",
                    ""
                )
                .strip()
            )


            assessment_type = (
                request.POST.get(
                    f"assessment_type_{index}",
                    ""
                )
                .strip()
            )


            assessment_details = (
                request.POST.get(
                    f"assessment_details_{index}",
                    ""
                )
                .strip()
            )


            mark_value = (
                request.POST.get(
                    f"mark_{index}",
                    ""
                )
                .strip()
            )


            visibility_value = (
                request.POST.get(
                    f"visibility_{index}",
                    ""
                )
                .strip()
            )


            is_visible = (
                visibility_value == "1"
            )


            # Completely empty row.

            if (
                not entry_id
                and not assessment_type
                and not assessment_details
                and not mark_value
            ):

                continue


            rows.append(
                {
                    "entry_id": entry_id,
                    "assessment_type": assessment_type,
                    "assessment_details": assessment_details,
                    "mark_value": mark_value,
                    "is_visible": is_visible,
                }
            )


        # =================================================
        # SAVE EACH ROW
        # =================================================

        for row in rows:

            entry_id = row["entry_id"]


            if entry_id:

                entry = get_object_or_404(
                    GradebookEntry,
                    id=entry_id,
                    student=student,
                    course_unit=selected_unit
                )

            else:

                entry = GradebookEntry(
                    student=student,
                    course_unit=selected_unit
                )


            assessment_type = (
                row["assessment_type"]
            )


            # Default assessment type for new rows.

            if not assessment_type:

                assessment_type = (
                    f"Assessment {len(submitted_entry_ids) + 1}"
                )


            entry.assessment_type = (
                assessment_type
            )


            entry.assessment_details = (
                row["assessment_details"]
            )


            # =================================================
            # MARK
            # =================================================

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


            # =================================================
            # VISIBILITY
            # =================================================

            entry.is_visible = (
                row["is_visible"]
            )


            # =================================================
            # FINAL GRADE
            #
            # The same final grade is stored on the gradebook
            # entries so that the student gradebook can retrieve
            # it independently of individual row visibility.
            # =================================================

            entry.final_grade = final_grade


            entry.save()


            submitted_entry_ids.append(
                entry.id
            )


        # =====================================================
        # DELETE OLD ROWS THAT WERE REMOVED
        # =====================================================

        GradebookEntry.objects.filter(
            student=student,
            course_unit=selected_unit
        ).exclude(
            id__in=submitted_entry_ids
        ).delete()


        messages.success(
            request,
            "Gradebook saved successfully."
        )


        return redirect(
            "student_gradebook",
            student_id=student.id
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
    # GET SAVED FINAL GRADE
    # =====================================================

    saved_final_grade = ""


    final_grade_entry = (
        GradebookEntry.objects
        .filter(
            student=student,
            course_unit=selected_unit
        )
        .exclude(
            final_grade=""
        )
        .exclude(
            final_grade__isnull=True
        )
        .first()
    ) if selected_unit else None


    if final_grade_entry:

        saved_final_grade = (
            final_grade_entry.final_grade
        )


    # =====================================================
    # RENDER LECTURER GRADEBOOK
    # =====================================================

    return render(
        request,
        "students/student_gradebook.html",
        {
            "student": student,

            "course_units": course_units,

            "selected_unit": selected_unit,

            "gradebook_entries": gradebook_entries,

            "saved_final_grade": saved_final_grade,
        }
    )


# =========================================================
# STUDENT SUBMIT ASSIGNMENT
# =========================================================

@login_required
def student_submit_assignment(
    request,
    assignment_id
):

    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )


    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        student=student,
        allow_student_access=True,
        allow_submission=True
    )


    if request.method == "POST":

        form = AssignmentSubmissionForm(
            request.POST,
            request.FILES
        )


        if form.is_valid():

            submission = form.save(
                commit=False
            )


            submission.assignment = (
                assignment
            )


            submission.save()


            messages.success(
                request,
                "Your assignment was submitted successfully."
            )


            return redirect(
                "student_dashboard"
            )


    else:

        form = AssignmentSubmissionForm()


    return render(
        request,
        "students/student_submit_assignment.html",
        {
            "student": student,
            "assignment": assignment,
            "form": form,
        }
    )