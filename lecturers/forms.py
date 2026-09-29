from django import forms
from django.contrib.auth.models import User

from .models import LecturerProfile


class LecturerCreationForm(forms.ModelForm):

    default_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Default Password"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
        ]

    def save(self, commit=True):

        user = super().save(commit=False)

        password = self.cleaned_data['default_password']

        user.set_password(password)

        if commit:
            user.save()

            LecturerProfile.objects.create(
                user=user,
                must_change_password=True
            )

        return user