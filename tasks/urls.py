from django.urls import path
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter

from .views import (
    ChapterViewSet,
    ContentNodeViewSet,
    ContentViewSet,
    CourseViewSet,
    LessonViewSet,
    PlayGameView,
    QuestionViewSet,
    SectionViewSet,
    TaskViewSet,
    DeleteCanvasImage,
    ComplaintViewSet,
)

router = routers.DefaultRouter()
router.register(r"courses", CourseViewSet)

courses_router = routers.NestedSimpleRouter(router, r"courses", lookup="course")
courses_router.register(r"sections", SectionViewSet, basename="course-sections")

sections_router = routers.NestedSimpleRouter(
    courses_router, r"sections", lookup="section"
)

sections_router.register(r"chapters", ChapterViewSet, basename="section-chapters")

chapters_router = routers.NestedSimpleRouter(
    sections_router, r"chapters", lookup="chapter"
)

chapters_router.register(
    r"content-nodes", ContentNodeViewSet, basename="chapter-content-nodes"
)
chapters_router.register(r"contents", ContentViewSet, basename="chapter-contents")
chapters_router.register(r"lessons", LessonViewSet, basename="chapter-lessons")
chapters_router.register(r"tasks", TaskViewSet, basename="chapter-tasks")

tasks_router = routers.NestedSimpleRouter(chapters_router, r"tasks", lookup="task")
tasks_router.register(r"questions", QuestionViewSet, basename="task-questions")

complaint_router = DefaultRouter()
complaint_router.register(r"complaints", ComplaintViewSet, basename="complaints")

urlpatterns = [
    path("play-game/", PlayGameView.as_view(), name="play-game"),
    path("canvas-images/", DeleteCanvasImage.as_view(), name="delete-canvas-image"),
]

urlpatterns += (
    router.urls
    + courses_router.urls
    + sections_router.urls
    + chapters_router.urls
    + tasks_router.urls
    + complaint_router.urls
)
