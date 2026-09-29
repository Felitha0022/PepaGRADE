from django import forms


class AIAssessmentForm(forms.Form):

    title = forms.CharField(
        label='Assignment Title',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter assignment title',
            }
        )
    )

    document_type = forms.ChoiceField(
        label='Assignment Type',
        choices=[
            ('essay', 'Essay Assignment'),
            ('proposal', 'Project Proposal'),
            ('literature_review', 'Literature Review'),
        ],
        widget=forms.Select(
            attrs={
                'class': 'form-control',
            }
        )
    )

    submission_file = forms.FileField(
        label='Student Paper',
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }
        )
    )

    marking_guide_title = forms.CharField(
        label='Marking Guide Title',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter marking guide title',
            }
        )
    )

    marking_guide_file = forms.FileField(
        label='Marking Guide',
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx',
            }
        )
    )