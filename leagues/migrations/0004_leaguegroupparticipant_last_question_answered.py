# Generated by Django 5.1 on 2025-04-14 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0003_leaguegroupparticipant_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaguegroupparticipant',
            name='last_question_answered',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
