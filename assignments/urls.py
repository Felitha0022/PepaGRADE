from django.urls import path

from .views import (
    create_assignment,
    student_assignments,
    assignment_detail,
    delete_assignment,
    upload_assignment_submission,
    upload_assignment_marking_guide,
    upload_submission,
    marking_guide_success,
)


urlpatterns = [

    path(
        'student/<int:student_id>/',
        student_assignments,
        name='student_assignments'
    ),

    path(
        'student/<int:student_id>/create/',
        create_assignment,
        name='create_assignment'
    ),

    path(
        '<int:assignment_id>/',
        assignment_detail,
        name='assignment_detail'
    ),

    path(
        '<int:assignment_id>/submission/upload/',
        upload_assignment_submission,
        name='upload_assignment_submission'
    ),

    path(
        '<int:assignment_id>/marking-guide/upload/',
        upload_assignment_marking_guide,
        name='upload_assignment_marking_guide'
    ),

    # Legacy upload route.
    # It redirects instead of creating an orphan submission.
    path(
        'upload/',
        upload_submission,
        name='upload_submission'
    ),

    path(
        'marking-guide/success/',
        marking_guide_success,
        name='marking_guide_success'
    ),

    path(
        '<int:assignment_id>/delete/',
        delete_assignment,
        name='delete_assignment'
    ),
]