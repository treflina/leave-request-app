from django.urls import path
from . import views

app_name = "sickleaves_app"

urlpatterns = [
    path('sickleaves/', views.SickleavesListView.as_view(), name='sickleaves'),
    path('add-sickleave/', views.SickleaveCreateView.as_view(), name='add-sickleave'),
    path('sickleave-delete/<pk>/', views.delete_sickleave, name='delete_sickleave'),
    path('sickleave-update/<pk>/', views.SickleaveUpdateView.as_view(), name='update_sickleave'),
]