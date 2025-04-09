from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, SubjectViewSet


router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"subjects", SubjectViewSet, basename="subject")
urlpatterns = router.urls
