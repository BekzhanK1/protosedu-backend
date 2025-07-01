from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TestCategoryViewSet,
    TestReviewAPIView,
    TestViewSet,
    QuestionViewSet,
    ContentViewSet,
    AnswerOptionViewSet,
    AnswerQuestionAPIView,
)

router = DefaultRouter()
router.register(r"test-categories", TestCategoryViewSet)
router.register(r"tests", TestViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"contents", ContentViewSet)
router.register(r"answer-options", AnswerOptionViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("answer-question/", AnswerQuestionAPIView.as_view(), name="answer-question"),
    path("test-review/", TestReviewAPIView.as_view(), name="test-review"),
]
