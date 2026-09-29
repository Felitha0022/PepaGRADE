
from django.db import models
from assessment.models import Assessment


class Report(models.Model):

    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='report'
    )

    title = models.CharField(
        max_length=250
    )

    report_content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title

    @property
    def student(self):
        return self.assessment.submission.assignment.student

    @property
    def student_name(self):
        return self.student.full_name

