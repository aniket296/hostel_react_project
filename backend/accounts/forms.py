from django import forms

class LoginForm(forms.Form):
    identifier = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Enter your username or phone number"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter password"
        })
    )