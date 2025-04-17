# Generated by Django 5.1 on 2025-04-17 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0010_alter_subject_grade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subject',
            name='grade',
            field=models.IntegerField(choices=[(-1, '-1'), (0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10'), (11, '11')], default=1),
        ),
    ]
