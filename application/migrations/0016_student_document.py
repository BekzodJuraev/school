# Generated by Django 4.1.2 on 2025-07-14 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0015_student_archive_student_prikaz_archive_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to='staff/'),
        ),
    ]
