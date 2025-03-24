# Generated by Django 4.2.19 on 2025-03-24 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0014_merge_20250324_1956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='correct_answer',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
