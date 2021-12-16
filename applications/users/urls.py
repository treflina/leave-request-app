from django.urls import path, reverse_lazy

from . import views

app_name = "users_app"

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='user-register'),
    path('login/', views.LoginUser.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('update/', views.UpdatePasswordView.as_view(), name='user-update'),
    path('all-employees/', views.AllEmployeesList.as_view(), name='all-employees'),
    path('admin-all-employees/', views.AdminEmployeesList.as_view(), name='admin-all-employees'),
    path('employee-delete/<int:pk>/', views.delete_employee, name='delete_employee'),
    path('employee-update/<int:pk>/', views.EmpleadoUpdateView.as_view(), name='update_employee'),
]