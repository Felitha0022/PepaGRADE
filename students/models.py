from django.db import models
from lecturers.models import LecturerProfile
from django.contrib.auth.models import User


# =========================================================
# STUDENT PROFILE
# =========================================================

class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )

    lecturer = models.ForeignKey(
        LecturerProfile,
        on_delete=models.CASCADE,
        related_name="students"
    )

    student_id = models.CharField(
        max_length=30,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    program = models.CharField(
        max_length=150
    )

    year_level = models.PositiveIntegerField()

    profile_picture = models.ImageField(
        upload_to='student_profiles/',
        blank=True,
        null=True
    )

    must_change_password = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


# =========================================================
# COURSE UNIT
# =========================================================

class CourseUnit(models.Model):

    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


# =========================================================
# ENROLLMENT
# =========================================================

class Enrollment(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    course_unit = models.ForeignKey(
        CourseUnit,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    enrolled_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "student",
            "course_unit"
        )

    def __str__(self):
        return f"{self.student} - {self.course_unit}"


# =========================================================
# GRADEBOOK ENTRY
# =========================================================

class GradebookEntry(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='gradebook_entries'
    )

    course_unit = models.ForeignKey(
        CourseUnit,
        on_delete=models.CASCADE,
        related_name='gradebook_entries'
    )

    # Lecturer manually enters the assessment name.
    assessment_type = models.CharField(
        max_length=100
    )

    # Lecturer can enter assessment details.
    assessment_details = models.TextField(
        blank=True
    )

    mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # =====================================================
    # OLD LECTURER GRADEBOOK FINAL GRADE FIELDS
    # =====================================================

    final_grade = models.CharField(
        max_length=10,
        blank=True
    )

    is_visible = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            'created_at'
        ]

    def __str__(self):

        return (
            f'{self.student.full_name} - '
            f'{self.course_unit.code} - '
            f'{self.assessment_type}'
        )