from django import forms
from .models import Clerk


class ClerkCreateForm(forms.ModelForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Clerk
        fields = [
            "full_name",
            "phone_number",
            "assigned_hostel",
        ]


class ClerkEditForm(forms.ModelForm):
    class Meta:
        model = Clerk
        fields = [
            "full_name",
            "phone_number",
            "assigned_hostel",
        ]