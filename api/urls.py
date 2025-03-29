from django.urls import include, path
from .views import stream_log

urlpatterns = [
    path("", include("account.urls")),
    path("", include("tasks.urls")),
    path("", include("subscription.urls")),
    path("", include("olympiad.urls")),
    path("modo/", include("modo.urls")),
    path("logs/", stream_log),
]
