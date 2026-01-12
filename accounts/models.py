from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_SEEKER = "job_seeker"
    ROLE_EMPLOYER = "employer"
    ROLE_ADMIN = "admin"

    ROLE_CHOICES = [
        (ROLE_SEEKER, "Job Seeker"),
        (ROLE_EMPLOYER, "Employer"),
        (ROLE_ADMIN, "Admin"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_SEEKER)
    company_name = models.CharField(max_length=160, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
