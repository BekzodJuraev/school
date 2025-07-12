from django.db import models
from django.contrib.auth.models import User

from django.contrib.auth.models import AbstractUser


class Profile(models.Model):
    POSITION_CHOICES = [
        ("admin", "Админ"),
        ("HR", "Отдел кадров"),
        ("zavuch", "Завуч"),


    ]
    username = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=200, null=True, blank=True, default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
    middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True, null=True)
    approve=models.BooleanField(default=False)

    def __str__(self):
        return self.name
