from django.contrib import admin

from .models import (
    LecturerProfile,
    ActivityLog,
     AdminProfile,
)


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'must_change_password',
        'created_at',
    )

    list_filter = (
        'must_change_password',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
    )


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'action',
        'description',
        'ip_address',
        'created_at',
    )

    list_filter = (
        'action',
        'created_at',
    )

    search_fields = (
        'user__username',
        'description',
    )

    readonly_fields = (
        'user',
        'action',
        'description',
        'ip_address',
        'created_at',
    )
@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'created_at',
    )

    readonly_fields = (
        'created_at',
    )