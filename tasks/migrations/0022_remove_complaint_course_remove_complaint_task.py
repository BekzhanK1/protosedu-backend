# Generated by Django 5.1 on 2025-04-15 23:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0021_complaint_course_complaint_task'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='complaint',
            name='course',
        ),
        migrations.RemoveField(
            model_name='complaint',
            name='task',
        ),
    ]
