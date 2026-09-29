from django.urls import path

from .views import (
    assess_assignment,
    assessment_result,
    assessment_dashboard,
    student_ai_assessment,
)


urlpatterns = [

    path(
        '',
        assessment_dashboard,
        name='assessment_dashboard'
    ),

    path(
        'student/<int:student_id>/',
        student_ai_assessment,
        name='student_ai_assessment'
    ),

    path(
        'assess/<int:submission_id>/',
        assess_assignment,
        name='assess_assignment'
    ),

    path(
        'result/<int:assessment_id>/',
        assessment_result,
        name='assessment_result'
    ),

]