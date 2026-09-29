from .models import AdminProfile


def admin_profile(request):

    if request.user.is_authenticated and request.user.is_superuser:

        profile, created = AdminProfile.objects.get_or_create(
            user=request.user
        )

        return {
            'admin_profile': profile
        }

    return {
        'admin_profile': None
    }