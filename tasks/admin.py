from django.contrib import admin

from .models import (
    Answer,
    Chapter,
    Complaint,
    Content,
    Course,
    Lesson,
    Question,
    Section,
    Task,
    TaskCompletion,
)


# Register Course model with customizations
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "grade", "created_by", "language")
    search_fields = ("name", "description", "created_by__email")
    list_filter = ("grade", "language")
    raw_id_fields = ("created_by",)


# Register Section model with customizations
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    search_fields = ("title", "course__name")
    list_filter = ("course",)
    ordering = ("course", "order")


# Register Content model with customizations
@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "order", "content_type")
    search_fields = ("title", "description", "chapter__title")
    list_filter = ("content_type", "chapter__section__course__name")
    ordering = ("chapter", "order")


# Register Lesson model with customizations
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "order")
    search_fields = ("title", "description", "chapter__title")
    list_filter = ("chapter__section__course__name",)
    ordering = ("chapter", "order")


# Register Task model with customizations
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "order")
    search_fields = ("title", "description", "chapter__title")
    list_filter = ("chapter__section__course__name",)
    ordering = ("chapter", "order")


# Register Question model with customizations
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "task", "question_type")
    search_fields = ("title", "question_text", "task__title")
    list_filter = ("question_type", "task__chapter__section__course__name")


# Register Answer model with customizations
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("user", "child", "question", "is_correct")
    search_fields = ("user__email", "child__first_name", "question__title")
    list_filter = ("is_correct", "question__task__chapter__section__course__name")
    raw_id_fields = ("user", "child", "question")


# Register TaskCompletion model with customizations
@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "child", "task", "correct", "wrong", "completed_at")
    search_fields = ("user__email", "child__first_name", "task__title")
    list_filter = ("task__chapter__section__course__name", "completed_at")
    raw_id_fields = ("user", "child", "task")


admin.site.register(Chapter)
admin.site.register(Complaint)
