from django.contrib import admin
from .models import (
    Test,
    Question,
    Content,
    AnswerOption,
    TestAnswer,
    TestResult,
    TestCategory,
)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "description",
        "test_type",
        "get_language",
        "category",
        "order",
    )
    list_select_related = ("category",)  # optimizes queries
    ordering = ("category__name", "order")  # first by category, then by order

    def get_language(self, obj):
        if obj.category:
            return obj.category.language
        return "-"

    get_language.short_description = "Language"


admin.site.register(Question)
admin.site.register(Content)
admin.site.register(AnswerOption)
admin.site.register(TestAnswer)
admin.site.register(TestResult)
admin.site.register(TestCategory)
