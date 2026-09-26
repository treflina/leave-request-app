from django.urls import path
from . import api, views

app_name = "requests_app"

urlpatterns = [
    path(
        "wniosek/",
        views.RequestFormView.as_view(),
        name="request",
    ),
    path(
        "zmienwniosek/<int:pk>/",
        views.RequestChangeView.as_view(),
        name="changerequest",
    ),
    path(
        "wnioskipracownika/",
        views.UserRequestsListView.as_view(),
        name="user_requests",
    ),
    path(
        "wnioskipracownika/urlop/",
        views.UserHolidayRequestsListView.as_view(),
        name="user_holiday_requests",
    ),
    path(
        "wnioskipracownika/dniwolne/",
        views.UserOtherRequestsListView.as_view(),
        name="user_other_requests",
    ),
    path(
        "wnioski/",
        views.RequestsListView.as_view(),
        name="allrequests",
    ),
    path(
        "wnioski-do-zaakceptowania/",
        views.RequestsToAcceptListView.as_view(),
        name="requests_to_accept",
    ),
    path(
        "hrwnioski/",
        views.HRAllRequestsListView.as_view(),
        name="hrallrequests",
    ),
    path(
        "wniosek-odrzuc/<int:pk>/",
        views.reject_request,
        name="reject_request",
    ),
    path(
        "wniosek-zaakceptuj/<int:pk>/",
        views.accept_request,
        name="accept_request",
    ),
    path(
        "wniosek-usun/<int:pk>/",
        views.delete_request,
        name="delete_request",
    ),
    path(
        "api/hr/leaves/<int:year>/<int:month>/",
        api.hr_leave_month_api,
        name="hr_leave_month_api",
    ),
]
