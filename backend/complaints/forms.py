from django import forms
from .models import Complaint


class ComplaintCreateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["description"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter complaint description",
                }
            )
        }

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise forms.ValidationError("Complaint description is required.")
        return description

class AssignWorkerForm(forms.Form):
    worker_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter worker name"}),
    )


class ComplaintFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[("", "All Statuses")] + Complaint.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )