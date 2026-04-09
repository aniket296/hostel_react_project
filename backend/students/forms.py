from django import forms
from .models import Department, Student


class StudentCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text="Set the student's login password."
    )

    def __init__(self, *args, **kwargs):
        allowed_gender = kwargs.pop("allowed_gender", None)
        super().__init__(*args, **kwargs)
        if allowed_gender:
            allowed = [choice for choice in Student.GENDER_CHOICES if choice[0] == allowed_gender]
            self.fields["gender"].choices = allowed
            self.fields["gender"].initial = allowed_gender

    class Meta:
        model = Student
        fields = [
            "full_name",
            "phone_number",
            "department",
            "year",
            "gender",
            "room_number",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-control"}),
            "year": forms.Select(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "room_number": forms.TextInput(attrs={"class": "form-control"}),
        }


class StudentEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        allowed_gender = kwargs.pop("allowed_gender", None)
        super().__init__(*args, **kwargs)
        if allowed_gender:
            allowed = [choice for choice in Student.GENDER_CHOICES if choice[0] == allowed_gender]
            self.fields["gender"].choices = allowed
            self.fields["gender"].initial = allowed_gender

    class Meta:
        model = Student
        fields = [
            "full_name",
            "phone_number",
            "department",
            "year",
            "gender",
            "room_number",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-control"}),
            "year": forms.Select(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "room_number": forms.TextInput(attrs={"class": "form-control"}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"})
        }


class StudentImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )


class BulkDeleteStudentsForm(forms.Form):
    student_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.MultipleHiddenInput
    )

    def __init__(self, *args, **kwargs):
        student_choices = kwargs.pop("student_choices", [])
        super().__init__(*args, **kwargs)
        self.fields["student_ids"].choices = student_choices