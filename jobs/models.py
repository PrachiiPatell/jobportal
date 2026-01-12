from django.db import models
from django.conf import settings

class Job(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField()
    company = models.CharField(max_length=160)
    category = models.CharField(max_length=80)
    location = models.CharField(max_length=120)
    salary = models.IntegerField(blank=True, null=True)

    # internal controls
    is_active = models.BooleanField(default=True)
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs")
    created_at = models.DateTimeField(auto_now_add=True)

    # --- API Imported Job Fields ---
    is_external = models.BooleanField(default=False, db_index=True)
    external_source = models.CharField(max_length=50, blank=True, null=True, db_index=True)  # e.g. "arbeitnow"
    external_id = models.CharField(max_length=200, blank=True, null=True)  # e.g. slug
    external_url = models.URLField(blank=True, null=True)
    remote = models.BooleanField(default=False, db_index=True)
    external_created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["external_source", "external_id"],
                name="uniq_external_source_id"
            )
        ]

    def __str__(self):
        return self.title


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "applicant")

    def __str__(self):
        return f"{self.applicant} -> {self.job}"
