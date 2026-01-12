from django import forms
from .models import Job, Application

CATEGORY_CHOICES = [
    ("Software", "Software"),
    ("Data", "Data"),
    ("Design", "Design"),
    ("Marketing", "Marketing"),
    ("Sales", "Sales"),
    ("HR", "HR"),
    ("Other", "Other"),
]

class JobForm(forms.ModelForm):
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)

    class Meta:
        model = Job
        fields = ["title", "company", "category", "location", "salary", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 8}),
        }

class ApplyForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter"]
        widgets = {"cover_letter": forms.Textarea(attrs={"rows": 8})}
