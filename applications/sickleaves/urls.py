from django.urls import path
from . import views

app_name = "sickleaves_app"

urlpatterns = [
    path(
        "allsickleaves/",
        views.SickleavesListView.as_view(),
        name="sickleaves"
        ),
    path(
        "add-sickleave/",
        views.SickleaveCreateView.as_view(),
        name="add-sickleave",
    ),
    path(
        "sickleave-delete/<pk>/",
        views.delete_sickleave,
        name="delete_sickleave",
    ),
    path(
        "sickleave-update/<pk>/",
        views.SickleaveUpdateView.as_view(),
        name="update_sickleave",
    ),
    path(
        "sickleave-notification/<pk>/",
        views.notify_about_sickleave,
        name="notify_sickleave",
    ),
    path("ezla/", views.get_ezla, name="get_ezla"),
]
