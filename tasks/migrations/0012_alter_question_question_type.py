# Generated by Django 4.2.20 on 2025-03-23 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_remove_answer_answer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('multiple_choice_text', 'Multiple Choice Text'), ('multiple_choice_images', 'Multiple Choice Images'), ('drag_and_drop_text', 'Drag and Drop Text'), ('drag_and_drop_images', 'Drag and Drop Images'), ('true_false', 'True or False'), ('mark_all', 'Mark All That Apply'), ('number_line', 'Number Line'), ('drag_position', 'Drag Position'), ('click_image', 'Click Image'), ('input_text', 'Input Text')], max_length=50),
        ),
    ]
