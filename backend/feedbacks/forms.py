from django import forms

from .models import FeedbackForm


class FeedbackFormCreateForm(forms.ModelForm):
    class Meta:
        model = FeedbackForm
        fields = ["name", "hostel", "duration_hours"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "hostel": forms.Select(attrs={"class": "form-control"}),
            "duration_hours": forms.Select(attrs={"class": "form-control"}),
        }