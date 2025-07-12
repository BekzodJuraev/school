from django.contrib import admin
from .models import Profile
from django.utils.html import format_html
# Register your models here.


@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ['name','approve']