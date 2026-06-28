from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    ADMINISTRATOR = 'ADMINISTRATOR', 'Administrator'
    RESEARCHER = 'RESEARCHER', 'Researcher'
    REVIEWER = 'REVIEWER', 'Reviewer'
    READ_ONLY = 'READ_ONLY', 'Read-Only Internal User'

class User(AbstractUser):
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.RESEARCHER,
        help_text="Role determining verification, extraction, and merge permissions."
    )
    title = models.CharField(max_length=100, blank=True)
    organization_affiliation = models.CharField(max_length=200, blank=True)

    def is_reviewer_or_admin(self):
        return self.role in [UserRole.REVIEWER, UserRole.ADMINISTRATOR] or self.is_superuser
