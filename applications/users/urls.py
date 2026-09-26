from django.urls import path

from . import views

app_name = "users_app"

urlpatterns = [
    path("register/", views.UserRegisterView.as_view(), name="user-register"),
    path("login/", views.LoginUser.as_view(), name="user-login"),
    path("logout/", views.LogoutView.as_view(), name="user-logout"),
    path("zmien-haslo/", views.update_password, name="user-update"),
    path(
        "email-settings/<int:pk>/",
        views.email_notifications_settings,
        name="email-settings"
        ),
    path(
        "pracownicy/",
        views.AllEmployeesList.as_view(),
        name="all-employees"
        ),
    path(
        "admin-pracownicy/",
        views.AdminEmployeesList.as_view(),
        name="admin-all-employees",
    ),
    path(
        "byli-pracownicy/",
        views.FormerEmployeesList.as_view(),
        name="former-employees",
    ),
    path(
        "pracownik-usun/<int:pk>/",
        views.delete_employee,
        name="delete_employee"
        ),
    path(
        "pracownik-edycja/<int:pk>/",
        views.EmployeeUpdateView.as_view(),
        name="update_employee",
    ),
    path(
        "add-annual-leave/",
        views.add_annual_leave,
        name="add_annual_leave",
    ),
    path(
        "subscription-check/",
        views.subscription_check,
        name="subscription-check"
        ),
]
