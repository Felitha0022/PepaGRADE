from django.contrib import messages

from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash
)

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .forms import LecturerCreationForm

from .models import (
    LecturerProfile,
    AdminProfile,
    ActivityLog
)

from students.models import StudentProfile


# =========================================================
# LANDING PAGE
# =========================================================

def landing_page(request):

    return render(
        request,
        'landing.html'
    )


# =========================================================
# ADMIN SIGN UP
# =========================================================

def admin_signup(request):

    # Only allow registration if no administrator exists.
    if User.objects.filter(is_superuser=True).exists():

        messages.info(
            request,
            'An administrator account already exists. '
            'Please log in.'
        )

        return redirect(
            'admin_login'
        )

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()

        first_name = request.POST.get(
            'first_name',
            ''
        ).strip()

        last_name = request.POST.get(
            'last_name',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        password = request.POST.get(
            'password',
            ''
        )

        confirm_password = request.POST.get(
            'confirm_password',
            ''
        )

        if not username:

            messages.error(
                request,
                'Please enter a username.'
            )

        elif not password:

            messages.error(
                request,
                'Please enter a password.'
            )

        elif password != confirm_password:

            messages.error(
                request,
                'Passwords do not match.'
            )

        elif len(password) < 8:

            messages.error(
                request,
                'Password must contain at least 8 characters.'
            )

        elif User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                'That username is already in use.'
            )

        else:

            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            ActivityLog.objects.create(
                user=user,
                action='signup',
                description=(
                    'Administrator account was created.'
                ),
                ip_address=request.META.get(
                    'REMOTE_ADDR'
                ),
            )

            login(
                request,
                user
            )

            messages.success(
                request,
                'Administrator account created successfully.'
            )

            return redirect(
                'admin_dashboard'
            )

    return render(
        request,
        'admin_signup.html'
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

def admin_login(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:

            return redirect(
                'admin_dashboard'
            )

        logout(request)

    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_superuser:

            login(
                request,
                user
            )

            ActivityLog.objects.create(
                user=user,
                action='login',
                description=(
                    'Administrator logged into PepaGRADE.'
                ),
                ip_address=request.META.get(
                    'REMOTE_ADDR'
                ),
            )

            return redirect(
                'admin_dashboard'
            )

        messages.error(
            request,
            'Invalid administrator username or password.'
        )

    return render(
        request,
        'admin_login.html'
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have administrator permission.'
        )

        return redirect(
            'lecturer_login'
        )

    lecturer_count = User.objects.filter(
        lecturer_profile__isnull=False
    ).count()

    active_lecturer_count = User.objects.filter(
        lecturer_profile__isnull=False,
        is_active=True
    ).count()

    inactive_lecturer_count = User.objects.filter(
        lecturer_profile__isnull=False,
        is_active=False
    ).count()

    # Only the 10 most recent activities.
    recent_activity = ActivityLog.objects.select_related(
        'user'
    ).order_by(
        '-created_at'
    )[:10]

    # All activity logs for the "View All Activity" section.
    all_activity = ActivityLog.objects.select_related(
        'user'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'admin_dashboard.html',
        {
            'lecturer_count': lecturer_count,
            'active_lecturer_count': active_lecturer_count,
            'inactive_lecturer_count': inactive_lecturer_count,
            'recent_activity': recent_activity,
            'all_activity': all_activity,
        }
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@login_required
def admin_logout(request):

    if not request.user.is_superuser:

        return redirect(
            'lecturer_dashboard'
        )

    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        description=(
            'Administrator logged out of PepaGRADE.'
        ),
        ip_address=request.META.get(
            'REMOTE_ADDR'
        ),
    )

    logout(request)

    return redirect(
        'admin_login'
    )


# =========================================================
# LECTURER LOGIN
# =========================================================

def lecturer_login(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:

            return redirect(
                'admin_dashboard'
            )

        if hasattr(
            request.user,
            'lecturer_profile'
        ):

            return redirect(
                'lecturer_dashboard'
            )

        logout(request)

    if request.method == 'POST':

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Only lecturers can use lecturer login.
            if not hasattr(
                user,
                'lecturer_profile'
            ):

                messages.error(
                    request,
                    'This account is not registered as a lecturer.'
                )

                return redirect(
                    'lecturer_login'
                )

            login(
                request,
                user
            )

            ActivityLog.objects.create(
                user=user,
                action='login',
                description=(
                    'Lecturer logged into PepaGRADE.'
                ),
                ip_address=request.META.get(
                    'REMOTE_ADDR'
                ),
            )

            profile = user.lecturer_profile

            if profile.must_change_password:

                return redirect(
                    'change_lecturer_password'
                )

            return redirect(
                'lecturer_dashboard'
            )

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(
        request,
        'lecturers/login.html'
    )


# =========================================================
# LECTURER DASHBOARD
# =========================================================

@login_required
def lecturer_dashboard(request):

    # Administrators should use the admin dashboard.
    if request.user.is_superuser:

        return redirect(
            'admin_dashboard'
        )

    # Only lecturers can access this dashboard.
    if not hasattr(
        request.user,
        'lecturer_profile'
    ):

        logout(request)

        return redirect(
            'lecturer_login'
        )

    # Get the currently logged-in lecturer's profile.
    lecturer = request.user.lecturer_profile

    # IMPORTANT:
    # Only retrieve students belonging to this lecturer.
    students = StudentProfile.objects.filter(
        lecturer=lecturer
    ).order_by(
        'full_name'
    )

    return render(
        request,
        'lecturers/dashboard.html',
        {
            'students': students,
            'lecturer': lecturer,
        }
    )


# =========================================================
# CHANGE LECTURER PASSWORD
# =========================================================

@login_required
def change_lecturer_password(request):

    if not hasattr(
        request.user,
        'lecturer_profile'
    ):

        return redirect(
            'lecturer_login'
        )

    profile = request.user.lecturer_profile

    if request.method == 'POST':

        new_password = request.POST.get(
            'new_password'
        )

        confirm_password = request.POST.get(
            'confirm_password'
        )

        if not new_password:

            messages.error(
                request,
                'Please enter a new password.'
            )

        elif new_password != confirm_password:

            messages.error(
                request,
                'Passwords do not match.'
            )

        elif len(new_password) < 8:

            messages.error(
                request,
                'Password must contain at least 8 characters.'
            )

        else:

            request.user.set_password(
                new_password
            )

            request.user.save()

            profile.must_change_password = False

            profile.save()

            login(
                request,
                request.user
            )

            ActivityLog.objects.create(
                user=request.user,
                action='password_change',
                description=(
                    'Lecturer changed their password.'
                ),
                ip_address=request.META.get(
                    'REMOTE_ADDR'
                ),
            )

            messages.success(
                request,
                'Your password has been changed successfully.'
            )

            return redirect(
                'lecturer_dashboard'
            )

    return render(
        request,
        'lecturers/change_password.html'
    )


# =========================================================
# LECTURER LOGOUT
# =========================================================

@login_required
def lecturer_logout(request):

    if hasattr(
        request.user,
        'lecturer_profile'
    ):

        ActivityLog.objects.create(
            user=request.user,
            action='logout',
            description=(
                'Lecturer logged out of PepaGRADE.'
            ),
            ip_address=request.META.get(
                'REMOTE_ADDR'
            ),
        )

    logout(request)

    return redirect(
        'lecturer_login'
    )


# =========================================================
# CREATE LECTURER
# =========================================================

@login_required
def create_lecturer(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have permission to create lecturer accounts.'
        )

        return redirect(
            'lecturer_dashboard'
        )

    if request.method == 'POST':

        form = LecturerCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            ActivityLog.objects.create(
                user=request.user,
                action='create_lecturer',
                description=(
                    f'Created lecturer account '
                    f'"{user.username}".'
                ),
                ip_address=request.META.get(
                    'REMOTE_ADDR'
                ),
            )

            messages.success(
                request,
                f'Lecturer "{user.username}" '
                f'was created successfully.'
            )

            return redirect(
                'lecturer_list'
            )

    else:

        form = LecturerCreationForm()

    return render(
        request,
        'lecturers/create_lecturer.html',
        {
            'form': form
        }
    )


# =========================================================
# LECTURER LIST
# =========================================================

@login_required
def lecturer_list(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have permission to view lecturers.'
        )

        return redirect(
            'lecturer_dashboard'
        )

    lecturers = User.objects.filter(
        lecturer_profile__isnull=False
    ).select_related(
        'lecturer_profile'
    )

    return render(
        request,
        'lecturers/lecturer_list.html',
        {
            'lecturers': lecturers
        }
    )


# =========================================================
# ACTIVATE / DEACTIVATE LECTURER
# =========================================================

@login_required
def toggle_lecturer_status(request, lecturer_id):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have permission to manage lecturers.'
        )

        return redirect(
            'lecturer_dashboard'
        )

    lecturer = get_object_or_404(
        User,
        id=lecturer_id,
        lecturer_profile__isnull=False
    )

    lecturer.is_active = not lecturer.is_active

    lecturer.save()

    status = (
        'activated'
        if lecturer.is_active
        else 'deactivated'
    )

    ActivityLog.objects.create(
        user=request.user,
        action='other',
        description=(
            f'Lecturer "{lecturer.username}" '
            f'was {status}.'
        ),
        ip_address=request.META.get(
            'REMOTE_ADDR'
        ),
    )

    messages.success(
        request,
        f'Lecturer "{lecturer.username}" '
        f'was {status}.'
    )

    return redirect(
        'lecturer_list'
    )


# =========================================================
# DELETE LECTURER
# =========================================================

@login_required
def delete_lecturer(request, lecturer_id):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have permission to delete lecturer accounts.'
        )

        return redirect(
            'lecturer_dashboard'
        )

    if request.method != 'POST':

        messages.error(
            request,
            'Invalid request. Lecturer accounts can only be deleted using the delete button.'
        )

        return redirect(
            'lecturer_list'
        )

    lecturer = get_object_or_404(
        User,
        id=lecturer_id,
        lecturer_profile__isnull=False
    )

    lecturer_username = lecturer.username

    lecturer.delete()

    ActivityLog.objects.create(
        user=request.user,
        action='other',
        description=(
            f'Lecturer account "{lecturer_username}" was deleted.'
        ),
        ip_address=request.META.get(
            'REMOTE_ADDR'
        )
    )

    messages.success(
        request,
        f'Lecturer account "{lecturer_username}" was deleted successfully.'
    )

    return redirect(
        'lecturer_list'
    )

# =========================================================
# ADMIN ACTIVITY
# =========================================================

@login_required
def admin_activity(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have administrator permission.'
        )

        return redirect(
            'lecturer_login'
        )

    activities = ActivityLog.objects.select_related(
        'user'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'lecturers/admin_activity.html',
        {
            'activities': activities
        }
    )


# =========================================================
# DELETE ONE ACTIVITY LOG
# =========================================================

@login_required
def delete_activity(request, activity_id):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have permission to delete activity logs.'
        )

        return redirect(
            'lecturer_login'
        )

    if request.method != 'POST':

        messages.error(
            request,
            'Invalid request.'
        )

        return redirect(
            'admin_activity'
        )

    activity = get_object_or_404(
        ActivityLog,
        id=activity_id
    )

    activity.delete()

    messages.success(
        request,
        'Activity log deleted successfully.'
    )

    return redirect(
        'admin_activity'
    )


# =========================================================
# DELETE ALL ACTIVITY LOGS
# =========================================================

@login_required
def clear_activity(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have permission to delete activity logs.'
        )

        return redirect(
            'lecturer_login'
        )

    if request.method != 'POST':

        messages.error(
            request,
            'Invalid request.'
        )

        return redirect(
            'admin_activity'
        )

    ActivityLog.objects.all().delete()

    messages.success(
        request,
        'All activity logs have been deleted.'
    )

    return redirect(
        'admin_activity'
    )

# =========================================================
# ADMIN ACCOUNT
# =========================================================

@login_required
def admin_account(request):

    if not request.user.is_superuser:

        messages.error(
            request,
            'You do not have administrator permission.'
        )

        return redirect(
            'lecturer_login'
        )

    # Get or create the administrator's own profile.
    profile, created = AdminProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        action = request.POST.get(
            'action'
        )

        # =================================================
        # UPDATE PROFILE
        # =================================================

        if action == 'update_profile':

            first_name = request.POST.get(
                'first_name',
                ''
            ).strip()

            last_name = request.POST.get(
                'last_name',
                ''
            ).strip()

            email = request.POST.get(
                'email',
                ''
            ).strip()

            username = request.POST.get(
                'username',
                ''
            ).strip()

            if not username:

                messages.error(
                    request,
                    'Username cannot be empty.'
                )

            elif User.objects.filter(
                username=username
            ).exclude(
                id=request.user.id
            ).exists():

                messages.error(
                    request,
                    'That username is already in use.'
                )

            else:

                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.username = username

                request.user.save()

                if request.FILES.get(
                    'profile_picture'
                ):

                    profile.profile_picture = request.FILES[
                        'profile_picture'
                    ]

                    profile.save()

                ActivityLog.objects.create(
                    user=request.user,
                    action='other',
                    description=(
                        'Administrator updated account information.'
                    ),
                    ip_address=request.META.get(
                        'REMOTE_ADDR'
                    )
                )

                messages.success(
                    request,
                    'Account information updated successfully.'
                )

                return redirect(
                    'admin_account'
                )

        # =================================================
        # CHANGE PASSWORD
        # =================================================

        elif action == 'change_password':

            current_password = request.POST.get(
                'current_password',
                ''
            )

            new_password = request.POST.get(
                'new_password',
                ''
            )

            confirm_password = request.POST.get(
                'confirm_password',
                ''
            )

            if not request.user.check_password(
                current_password
            ):

                messages.error(
                    request,
                    'The current password is incorrect.'
                )

            elif not new_password:

                messages.error(
                    request,
                    'Please enter a new password.'
                )

            elif new_password != confirm_password:

                messages.error(
                    request,
                    'Passwords do not match.'
                )

            elif len(new_password) < 8:

                messages.error(
                    request,
                    'Password must contain at least 8 characters.'
                )

            else:

                request.user.set_password(
                    new_password
                )

                request.user.save()

                # Keep the administrator logged in.
                update_session_auth_hash(
                    request,
                    request.user
                )

                ActivityLog.objects.create(
                    user=request.user,
                    action='password_change',
                    description=(
                        'Administrator changed their password.'
                    ),
                    ip_address=request.META.get(
                        'REMOTE_ADDR'
                    )
                )

                messages.success(
                    request,
                    'Password changed successfully.'
                )

                return redirect(
                    'admin_account'
                )

    return render(
        request,
        'lecturers/admin_account.html',
        {
            'profile': profile
        }
    )