from django.db import models
from students.models import StudentProfile


class Assignment(models.Model):

    DOCUMENT_TYPES = [
        ('essay', 'Essay Assignment'),
        ('proposal', 'Project Proposal'),
        ('literature_review', 'Literature Review'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    course_unit = models.ForeignKey(
        'students.CourseUnit',
        on_delete=models.CASCADE,
        related_name='assignments',
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=200
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES
    )

    description = models.TextField(
        blank=True
    )

    allow_student_access = models.BooleanField(
        default=False
    )

    allow_submission = models.BooleanField(
        default=False
    )

    due_date = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.title} - {self.student.student_id}"


class MarkingGuide(models.Model):

    assignment = models.OneToOneField(
        Assignment,
        on_delete=models.CASCADE,
        related_name='marking_guide'
    )

    title = models.CharField(
        max_length=200
    )

    file = models.FileField(
        upload_to='marking_guides/'
    )

    extracted_text = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    file = models.FileField(
        upload_to='assignments/'
    )

    extracted_text = models.TextField(
        blank=True
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.assignment.title} - Submission"