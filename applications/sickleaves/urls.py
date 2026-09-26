from django.urls import path
from . import views

app_name = "sickleaves_app"

urlpatterns = [
    path(
        "zwolnienia/",
        views.SickleavesListView.as_view(),
        name="sickleaves"
        ),
    path(
        "zwolnienie-dodaj/",
        views.SickleaveCreateView.as_view(),
        name="add-sickleave",
    ),
    path(
        "zwolnienie-usun/<pk>/",
        views.delete_sickleave,
        name="delete_sickleave",
    ),
    path(
        "zwolnienie-edycja/<pk>/",
        views.SickleaveUpdateView.as_view(),
        name="update_sickleave",
    ),
    path(
        "zwolnienie-powiadomienie/<pk>/",
        views.notify_about_sickleave,
        name="notify_sickleave",
    ),
    path("ezla/", views.get_ezla, name="get_ezla"),
]