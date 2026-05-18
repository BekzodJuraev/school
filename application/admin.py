from django.contrib import admin
from .models import Profile,Staff,Student,Warehouse,Invoice,Payment,Inventory,Inventory_cabinet,Inventory_items,Turniket,TrackingTurniket

from django.utils.html import format_html


@admin.register(TrackingTurniket)
class TrackingTurniket(admin.ModelAdmin):
    pass
@admin.register(Turniket)
class Turniket(admin.ModelAdmin):
    pass
@admin.register(Inventory)
class Inventory(admin.ModelAdmin):
    pass

@admin.register(Inventory_cabinet)
class Inventory_cabinet(admin.ModelAdmin):
    pass

@admin.register(Inventory_items)
class Inventory_items(admin.ModelAdmin):
    pass


@admin.register(Payment)
class Payment(admin.ModelAdmin):
    list_display = ['student','created_at','sum']
@admin.register(Invoice)
class Invoice(admin.ModelAdmin):
    list_display = ['warehouse']
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