# Generated by Django 4.2.13 on 2025-03-26 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_alter_child_grade_alter_class_grade_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='requires_password_change',
            field=models.BooleanField(default=False),
        ),
    ]
