from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenRefreshView

from account.views import *
from account.views.daily_message_views import DailyMessageView

children_router = SimpleRouter()
children_router.register(r"children", ChildrenViewSet, basename="children")


supervisor_school_router = SimpleRouter()
supervisor_school_router.register(
    r"supervisor_school", SupervisorSchoolViewset, basename="supervisor_school"
)

router = DefaultRouter()
router.register(r"schools", SchoolViewSet)


# Creating nested routing for classes within schools
schools_router = routers.NestedSimpleRouter(router, r"schools", lookup="school")
schools_router.register(r"classes", ClassViewSet, basename="school-classes")

# Creating nested routing for students within classes
classes_router = routers.NestedSimpleRouter(schools_router, r"classes", lookup="class")
classes_router.register(r"students", StudentViewSet, basename="class-students")

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("current-user/", CurrentUserView.as_view()),
    path("update-user/", UserUpdateView.as_view()),
    path("", include(supervisor_school_router.urls)),
    path("", include(children_router.urls)),
    path("", include(router.urls)),
    path("", include(schools_router.urls)),
    path("", include(classes_router.urls)),
    path("register-staff/", StaffRegistrationAPIView.as_view(), name="register-staff"),
    path(
        "register-parent/", ParentRegistrationAPIView.as_view(), name="register-parent"
    ),
    path("activate/<uuid:token>/", ActivateAccount.as_view(), name="activate_account"),
    path(
        "change-required-password/",
        ChangeRequiredPassword.as_view(),
        name="change-required-password",
    ),
    path("change-password/", ChangePassword.as_view(), name="change-password"),
    path(
        "reset-password/", RequestResetPassword.as_view(), name="request-reset-password"
    ),
    path(
        "reset-password/<uuid:token>/", ResetPassword.as_view(), name="reset-password"
    ),
    path("rating/<str:rating_type>/", TopStudentsView.as_view(), name="top_students"),
    path("all-students/", AllStudentsView.as_view(), name="all-students"),
    path("progress/weekly/", WeeklyProgressAPIView.as_view(), name="weekly-progress"),
    path("progress/day/", ProgressForSpecificDay.as_view(), name="daily-progress"),
    path("daily-message/", DailyMessageView.as_view(), name="daily-message"),
]
