# Generated by Django 5.1 on 2025-07-15 23:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modo', '0014_alter_answeroption_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answeroption',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='answer_options/images/'),
        ),
    ]
