from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(choices=[(User.ROLE_SEEKER, "Job Seeker"), (User.ROLE_EMPLOYER, "Employer")])
    company_name = forms.CharField(required=False, max_length=160)

    class Meta:
        model = User
        fields = ["username", "email", "role", "company_name", "password1", "password2"]

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
