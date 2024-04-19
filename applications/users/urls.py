from django.urls import path

from . import views

app_name = "users_app"

urlpatterns = [
    path("register/", views.UserRegisterView.as_view(), name="user-register"),
    path("login/", views.LoginUser.as_view(), name="user-login"),
    path("logout/", views.LogoutView.as_view(), name="user-logout"),
    path("update-password/", views.update_password, name="user-update"),
    path(
        "email-settings/<int:pk>/",
        views.email_notifications_settings,
        name="email-settings"
        ),
    path(
        "all-employees/",
        views.AllEmployeesList.as_view(),
        name="all-employees"
        ),
    path(
        "admin-all-employees/",
        views.AdminEmployeesList.as_view(),
        name="admin-all-employees",
    ),
    path(
        "employee-delete/<int:pk>/",
        views.delete_employee,
        name="delete_employee"
        ),
    path(
        "employee-update/<int:pk>/",
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
