# Generated by Django 5.1 on 2025-05-29 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0026_contentnode'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentnode',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contentnode',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
