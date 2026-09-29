from django import forms

from .models import (
    Assignment,
    AssignmentSubmission,
    MarkingGuide,
)


class AssignmentForm(forms.ModelForm):

    class Meta:
        model = Assignment

        fields = [
            'course_unit',
            'title',
            'document_type',
            'description',
            'allow_student_access',
            'allow_submission',
            'due_date',
        ]

        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': 5,
                    'placeholder': 'Enter assignment description...'
                }
            ),

            'due_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local'
                }
            ),
        }

        labels = {
            'course_unit': 'Course Unit',
            'allow_student_access': 'Allow Student Access',
            'allow_submission': 'Allow Submission',
            'due_date': 'Submission Due Date',
        }

    def __init__(self, *args, **kwargs):

        student = kwargs.pop('student', None)

        super().__init__(*args, **kwargs)

        if student:

            self.fields['course_unit'].queryset = (
                self.fields['course_unit'].queryset.filter(
                    enrollments__student=student
                ).distinct()
            )


class AssignmentSubmissionForm(forms.ModelForm):

    class Meta:
        model = AssignmentSubmission

        fields = [
            'file',
        ]


class MarkingGuideForm(forms.ModelForm):

    class Meta:
        model = MarkingGuide

        fields = [
            'title',
            'file',
        ]