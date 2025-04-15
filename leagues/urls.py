from django.urls import path
from .views import TestingView, CheckLeagueView, LeagueViewSet, LeagueGroupViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("leagues", LeagueViewSet, basename="league")
router.register("league-groups", LeagueGroupViewSet, basename="league-group")


urlpatterns = [
    # path("league/test/", TestingView.as_view(), name="test_league"),
    # path("league/check/", CheckLeagueView.as_view(), name="check_league"),
]
urlpatterns += router.urls
