from django.urls import path

from . import views

app_name = "home_app"

urlpatterns = [
    path("", views.HomePage.as_view(), name="index"),
    path("documents/", views.UploadFileView.as_view(), name="documents"),
    path("documents/<int:pk>/", views.delete_file, name="delete-file"),
]
