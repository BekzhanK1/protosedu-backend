# Generated by Django 4.2.13 on 2024-07-24 20:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.IntegerField(default=0)),
                ('content_type', models.CharField(choices=[('task', 'Task'), ('lesson', 'Lesson')], max_length=10)),
                ('video_url', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('grade', models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4')])),
                ('language', models.CharField(choices=[('ru', 'Russian'), ('kz', 'Kazakh'), ('en', 'English')], default='ru', max_length=50)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['grade'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('question_text', models.TextField()),
                ('question_type', models.CharField(choices=[('multiple_choice_text', 'Multiple Choice Text'), ('multiple_choice_images', 'Multiple Choice Images'), ('drag_and_drop_text', 'Drag and Drop Text'), ('drag_and_drop_images', 'Drag and Drop Images'), ('true_false', 'True or False'), ('mark_all', 'Mark All That Apply'), ('number_line', 'Number Line'), ('drag_position', 'Drag Position')], max_length=50)),
                ('options', models.JSONField(blank=True, null=True)),
                ('correct_answer', models.JSONField()),
                ('template', models.CharField(blank=True, default='1', max_length=20, null=True)),
                ('audio', models.FileField(blank=True, null=True, upload_to='audio/')),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.content')),
            ],
            bases=('tasks.content',),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tasks.content')),
            ],
            bases=('tasks.content',),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.IntegerField(default=0)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='tasks.course')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_id', models.PositiveIntegerField(blank=True, default=0, null=True)),
                ('image', models.ImageField(upload_to='questions/')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='tasks.question')),
            ],
        ),
        migrations.AddField(
            model_name='content',
            name='section',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='tasks.section'),
        ),
        migrations.AddField(
            model_name='question',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='tasks.task'),
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('is_correct', models.BooleanField()),
                ('child', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='account.child')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='tasks.question')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'question'), ('child', 'question')},
            },
        ),
        migrations.CreateModel(
            name='TaskCompletion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('correct', models.PositiveSmallIntegerField(default=0)),
                ('wrong', models.PositiveSmallIntegerField(default=0)),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('child', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='completed_tasks', to='account.child')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='completed_tasks', to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completed_by', to='tasks.task')),
            ],
            options={
                'unique_together': {('user', 'child', 'task')},
            },
        ),
    ]
