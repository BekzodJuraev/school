# Generated by Django 4.2.4 on 2025-02-15 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0007_teachers_status_alter_lesson_teacher'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='created_at',
            field=models.DateField(null=True),
        ),
    ]
