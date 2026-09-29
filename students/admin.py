from django.contrib import admin
from .models import StudentProfile, CourseUnit, Enrollment


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        'student_id',
        'full_name',
        'program',
        'year_level',
        'created_at',
    )

    search_fields = (
        'student_id',
        'full_name',
    )


@admin.register(CourseUnit)
class CourseUnitAdmin(admin.ModelAdmin):

    list_display = (
        'code',
        'name',
        'created_at',
    )

    search_fields = (
        'code',
        'name',
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'course_unit',
        'enrolled_at',
    )

    list_filter = (
        'course_unit',
    )

    search_fields = (
        'student__student_id',
        'student__full_name',
        'course_unit__code',
        'course_unit__name',
    )