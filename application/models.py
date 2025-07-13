from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
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
class SchoolClass(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g., "1-A", "2-B"

    def __str__(self):
        return self.name
class Student(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True, default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
    middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    phone = PhoneNumberField(blank=True, null=True)
    date_birth = models.DateField(null=True, blank=True, default=None)
    photo = models.ImageField(blank=True, null=True, upload_to='staff/')
    adres = models.CharField(max_length=200)
    passport = models.CharField(max_length=50)
    created_at = models.DateField(auto_now_add=True)
    prikaz=models.IntegerField(default=None)
    prikaz_date=models.DateField(blank=True,null=True)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True)
    Gender_CHOICES = [
        ("male", "Муж"),
        ("female", "Жен"),

    ]
    position_gender = models.CharField(max_length=20, choices=Gender_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.lastname} {self.name} - {self.school_class}"

class Staff(models.Model):
    POSITION_CHOICES = [
        ("teacher", "Учитель"),
        ("other", "Другое"),

    ]
    Gender_CHOICES = [
        ("male", "Муж"),
        ("female", "Жен"),

    ]

    name = models.CharField(max_length=200, null=True, blank=True, default=None)
    lastname = models.CharField(max_length=200, null=True, blank=True, default=None)
    middle_name = models.CharField(max_length=200, null=True, blank=True, default=None)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True, null=True)
    position_gender = models.CharField(max_length=20, choices=Gender_CHOICES, blank=True, null=True)
    date_birth = models.DateField(null=True, blank=True, default=None)
    phone = PhoneNumberField(blank=True,null=True)
    photo=models.ImageField(blank=True,null=True,upload_to='staff/')
    cv_rus=models.FileField(blank=True,null=True,upload_to='staff/')
    cv_uz= models.FileField(blank=True,null=True,upload_to='staff/')
    diplom = models.FileField(blank=True,null=True,upload_to='staff/')
    adres=models.CharField(max_length=200)
    passport=models.CharField(max_length=50)
    created_at=models.DateField(auto_now_add=True)
