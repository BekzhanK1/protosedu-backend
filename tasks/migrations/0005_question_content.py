# Generated by Django 5.1.6 on 2025-02-27 05:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_alter_chapter_options_alter_content_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='content',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
