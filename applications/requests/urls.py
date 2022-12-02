from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    path(
        "sendrequest/",
        views.RequestFormView.as_view(),
        name="request",
    ),
    path(
        "changerequest/<int:pk>/",
        views.RequestChangeView.as_view(),
        name="changerequest",
    ),
    path(
        "user-requests/",
        views.UserRequestsListView.as_view(),
        name="user_requests",
    ),
    path(
        "allrequests/",
        views.RequestsListView.as_view(),
        name="allrequests",
    ),
    path(
        "hrallrequests/",
        views.HRAllRequestsListView.as_view(),
        name="hrallrequests",
    ),
    path(
        "allholidayrequests/",
        views.AllHolidayRequestsListView.as_view(),
        name="allholidayrequests",
    ),
    path(
        "allotherrequests/",
        views.AllOtherRequestsListView.as_view(),
        name="allotherrequests",
    ),
    path(
        "request-reject/<int:pk>/",
        views.reject_request,
        name="reject_request",
    ),
    path(
        "request-accept/<int:pk>/",
        views.accept_request,
        name="accept_request",
    ),
    path(
        "request-delete/<int:pk>/",
        views.delete_request,
        name="delete_request",
    ),
]
