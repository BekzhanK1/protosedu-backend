from django.contrib import admin
from .models import Test, Question, Content, AnswerOption, TestAnswer

admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Content)
admin.site.register(AnswerOption)
admin.site.register(TestAnswer)
