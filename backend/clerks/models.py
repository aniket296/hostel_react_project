from django.conf import settings
from django.db import models


class Clerk(models.Model):
    HOSTEL_BOYS = "boys_hostel"
    HOSTEL_GIRLS = "girls_hostel"

    HOSTEL_CHOICES = [
        (HOSTEL_BOYS, "Boys Hostel"),
        (HOSTEL_GIRLS, "Girls Hostel"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clerk_profile"
    )
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    assigned_hostel = models.CharField(max_length=20, choices=HOSTEL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} - {self.get_assigned_hostel_display()}"