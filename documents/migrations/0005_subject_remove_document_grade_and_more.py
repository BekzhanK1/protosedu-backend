# Generated by Django 5.2 on 2025-04-09 20:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_alter_document_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('grade', models.CharField(choices=[(-1, '-1'), (0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4')], default='1', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='document',
            name='grade',
        ),
        migrations.RemoveField(
            model_name='document',
            name='preview_image',
        ),
        migrations.AddField(
            model_name='document',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(upload_to='documents/'),
        ),
        migrations.AddField(
            model_name='document',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='documents.subject'),
        ),
    ]
