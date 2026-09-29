from django.urls import path

from .views import (
    landing_page,
    admin_login,
    admin_signup,
    admin_dashboard,
    admin_logout,
    admin_activity,
    admin_account,
    delete_activity,
    clear_activity,
    lecturer_login,
    lecturer_dashboard,
    change_lecturer_password,
    lecturer_logout,
    create_lecturer,
    lecturer_list,
    toggle_lecturer_status,
    delete_lecturer,
)


urlpatterns = [

    # =====================================================
    # LANDING PAGE
    # =====================================================

    path(
        '',
        landing_page,
        name='landing_page'
    ),


    # =====================================================
    # ADMIN
    # =====================================================

    path(
        'admin/login/',
        admin_login,
        name='admin_login'
    ),

    path(
        'admin/signup/',
        admin_signup,
        name='admin_signup'
    ),

    path(
        'admin/dashboard/',
        admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'admin/logout/',
        admin_logout,
        name='admin_logout'
    ),

    path(
        'admin/lecturers/create/',
        create_lecturer,
        name='create_lecturer'
    ),

    path(
        'admin/lecturers/',
        lecturer_list,
        name='lecturer_list'
    ),

    path(
        'admin/lecturers/<int:lecturer_id>/toggle/',
        toggle_lecturer_status,
        name='toggle_lecturer_status'
    ),
    path(
    'admin/lecturers/<int:lecturer_id>/delete/',
    delete_lecturer,
    name='delete_lecturer'),

    path(
    'admin/activity/',
    admin_activity,
    name='admin_activity'
),

path(
    'admin/account/',
    admin_account,
    name='admin_account'
),

path(
    'admin/activity/<int:activity_id>/delete/',
    delete_activity,
    name='delete_activity'
),

path(
    'admin/activity/clear/',
    clear_activity,
    name='clear_activity'
),

    # =====================================================
    # LECTURER
    # =====================================================

    path(
        'login/',
        lecturer_login,
        name='lecturer_login'
    ),

    path(
        'dashboard/',
        lecturer_dashboard,
        name='lecturer_dashboard'
    ),

    path(
        'change-password/',
        change_lecturer_password,
        name='change_lecturer_password'
    ),

    path(
        'logout/',
        lecturer_logout,
        name='lecturer_logout'
    ),
]