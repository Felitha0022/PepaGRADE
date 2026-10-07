from django import forms

from .models import StudentProfile


class StudentProfileForm(forms.ModelForm):

    default_password = forms.CharField(
        label='Default Password',
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Generated automatically'
            }
        )
    )

    class Meta:
        model = StudentProfile

        fields = [
            'student_id',
            'full_name',
            'program',
            'year_level',
        ]

        widgets = {
            'student_id': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. 20240001',
                    'id': 'student_id'
                }
            ),
            'full_name': forms.TextInput(
                attrs={
                    'placeholder': 'Student full name'
                }
            ),
            'program': forms.TextInput(
                attrs={
                    'placeholder': 'e.g. Bachelor of Information Technology'
                }
            ),
            'year_level': forms.NumberInput(
                attrs={
                    'min': 1,
                    'max': 10
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        student_id = ''

        if self.is_bound:
            student_id = self.data.get(
                'student_id',
                ''
            )

        elif self.instance and self.instance.student_id:
            student_id = self.instance.student_id

        if student_id:
            self.fields['default_password'].initial = (
                f'{student_id}@DWU'
            )

# =========================================================
# STUDENT SELF PROFILE FORM
# =========================================================

class StudentSelfProfileForm(forms.ModelForm):

    class Meta:

        model = StudentProfile

        fields = [
            'full_name',
            'profile_picture',
        ]

        widgets = {

            'full_name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your full name',
                    'class': 'form-control'
                }
            ),

            'profile_picture': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),
        }

        labels = {

            'full_name': 'Full Name',

            'profile_picture': 'Profile Picture',

        }

class StudentEnrollmentForm(forms.Form):

    course_unit = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select a course unit"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from .models import CourseUnit

        self.fields['course_unit'].queryset = (
            CourseUnit.objects.all().order_by('code')
        )