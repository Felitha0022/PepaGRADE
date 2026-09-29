from django.contrib import admin

# Register your models here.
from .models import (
    Assignment,
    MarkingGuide,
    AssignmentSubmission
)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'student',
        'document_type',
        'created_at',
    )

    list_filter = ('document_type',)

    search_fields = ('title',)


@admin.register(MarkingGuide)
class MarkingGuideAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'assignment',
        'created_at',
    )


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):

    list_display = (
        'assignment',
        'submitted_at',
    )