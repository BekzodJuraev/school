# Generated by Django 4.2.4 on 2025-02-08 07:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0003_alter_attendance_options'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='attendance',
            table='logs',
        ),
    ]
