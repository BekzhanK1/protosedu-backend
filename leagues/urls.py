from django.urls import path
from .views import TestingView, CheckLeagueView

urlpatterns = [
    path("league/test/", TestingView.as_view(), name="test_league"),
    path("league/check/", CheckLeagueView.as_view(), name="check_league"),
]
