
from django.db import models
from assignments.models import AssignmentSubmission


class Assessment(models.Model):

    submission = models.OneToOneField(
        AssignmentSubmission,
        on_delete=models.CASCADE,
        related_name='assessment'
    )

    ai_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    ai_grade = models.CharField(
        max_length=10,
        blank=True
    )

    criterion_scores = models.JSONField(
        default=dict,
        blank=True
    )

    # Detailed AI analysis
    citation_analysis = models.JSONField(
        default=dict,
        blank=True
    )

    reference_analysis = models.JSONField(
        default=dict,
        blank=True
    )

    grammar_analysis = models.JSONField(
        default=dict,
        blank=True
    )

    academic_writing_analysis = models.JSONField(
        default=dict,
        blank=True
    )

    strengths = models.JSONField(
        default=list,
        blank=True
    )

    weaknesses = models.JSONField(
        default=list,
        blank=True
    )

    feedback = models.TextField(
        blank=True
    )

    lecturer_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    lecturer_feedback = models.TextField(
        blank=True
    )

    is_reviewed = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"Assessment - "
            f"{self.submission.assignment.title}"
        )

