from django.contrib import admin
from .models import Profile,Staff,Student,Warehouse
from django.utils.html import format_html
# Register your models here.

@admin.register(Warehouse)
class Warehouse(admin.ModelAdmin):
    list_display = ['name']
@admin.register(Student)
class Student(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Profile)
class Profile(admin.ModelAdmin):
    list_display = ['name','approve']

@admin.register(Staff)
class Staff(admin.ModelAdmin):
    list_display = ['name']