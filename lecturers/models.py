from django.db import models
from django.contrib.auth.models import User


# =========================================================
# LECTURER PROFILE
# =========================================================

class LecturerProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='lecturer_profile'
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )

    must_change_password = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# =========================================================
# ADMINISTRATOR PROFILE
# =========================================================

class AdminProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='admin_profile'
    )

    profile_picture = models.ImageField(
        upload_to='admin_profile_pictures/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.username


# =========================================================
# ACTIVITY LOG
# =========================================================

class ActivityLog(models.Model):

    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('signup', 'Administrator Sign Up'),
        ('create_lecturer', 'Create Lecturer'),
        ('password_change', 'Password Change'),
        ('create_student', 'Create Student'),
        ('create_assignment', 'Create Assignment'),
        ('assessment', 'AI Assessment'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES
    )

    description = models.TextField(
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):

        username = (
            self.user.username
            if self.user
            else 'Unknown User'
        )

        return (
            f"{username} - "
            f"{self.get_action_display()} - "
            f"{self.created_at}"
        )