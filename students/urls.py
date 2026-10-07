from django.urls import path

from .views import (
    student_list,
    student_create,
    student_detail,
    student_enroll,
    student_gradebook,
    student_login,
    student_dashboard,
    student_submit_assignment,
    student_change_password,
    student_logout,
    student_gradebook_page,
    student_delete,
    student_profile,
    student_account_details,
)


urlpatterns = [

    # =========================================================
    # STUDENT PORTAL
    # =========================================================

    path(
        'login/',
        student_login,
        name='student_login'
    ),

    path(
        'dashboard/',
        student_dashboard,
        name='student_dashboard'
    ),

    path(
        'gradebook/',
        student_gradebook_page,
        name='student_gradebook_page'
    ),

    path(
        'assignments/<int:assignment_id>/submit/',
        student_submit_assignment,
        name='student_submit_assignment'
    ),

    path(
        'change-password/',
        student_change_password,
        name='student_change_password'
    ),

        path(
        'profile/',
        student_profile,
        name='student_profile'
    ),

    path(
        'account-details/',
        student_account_details,
        name='student_account_details'
    ),

    path(
        'logout/',
        student_logout,
        name='student_logout'
    ),


    # =========================================================
    # LECTURER STUDENT MANAGEMENT
    # =========================================================

    path(
        '',
        student_list,
        name='student_list'
    ),

    path(
        'create/',
        student_create,
        name='student_create'
    ),

    path(
        '<int:student_id>/enroll/',
        student_enroll,
        name='student_enroll'
    ),

    path(
        '<int:student_id>/gradebook/',
        student_gradebook,
        name='student_gradebook'
    ),

    path(
        '<int:student_id>/delete/',
        student_delete,
        name='student_delete'
    ),

    path(
        '<int:student_id>/',
        student_detail,
        name='student_detail'
    ),
]