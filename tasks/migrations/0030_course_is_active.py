# Generated by Django 5.1 on 2025-06-11 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0029_remove_chapter_diagnostic_test_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
