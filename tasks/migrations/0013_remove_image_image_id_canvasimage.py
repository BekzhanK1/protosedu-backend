# Generated by Django 4.2.19 on 2025-03-22 11:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0012_image_image_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='image_id',
        ),
        migrations.CreateModel(
            name='CanvasImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_id', models.CharField(blank=True, max_length=100, null=True)),
                ('image', models.ImageField(upload_to='questions/')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='canvas_images', to='tasks.question')),
            ],
        ),
    ]
