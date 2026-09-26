from django.urls import path

from . import views

app_name = "home_app"

urlpatterns = [
    path("", views.HomePage.as_view(), name="index"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("dokumenty/", views.UploadFileView.as_view(), name="documents"),
    path("dokumenty/<int:pk>/", views.delete_file, name="delete-file"),
    path(
        "raport/",
        views.ReportView.as_view(),
        name="report",
    ),
]
