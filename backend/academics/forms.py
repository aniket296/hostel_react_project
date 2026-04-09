from django import forms
from .models import AcademicFile


class AcademicUploadForm(forms.ModelForm):
    subject_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    course_code = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        max_length=50,
    )

    class Meta:
        model = AcademicFile
        fields = [
            "subject_name",
            "course_code",
            "department",
            "year",
            "file_type",
            "file",
        ]
        widgets = {
            "department": forms.Select(attrs={"class": "form-control"}),
            "year": forms.Select(attrs={"class": "form-control"}),
            "file_type": forms.Select(attrs={"class": "form-control"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class AcademicEditForm(forms.ModelForm):
    subject_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    course_code = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        max_length=50,
    )

    class Meta:
        model = AcademicFile
        fields = [
            "subject_name",
            "course_code",
            "department",
            "year",
            "file_type",
            "file",
        ]
        widgets = {
            "department": forms.Select(attrs={"class": "form-control"}),
            "year": forms.Select(attrs={"class": "form-control"}),
            "file_type": forms.Select(attrs={"class": "form-control"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }