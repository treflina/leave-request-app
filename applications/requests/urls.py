from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    path(
        'sendrequest/', 
        views.RequestFormView.as_view(),
        name='request',
    ),
    path(
        'user-requests/', 
        views.UserRequestsListView.as_view(),
        name='user_requests',
    ),
    path(
        'allrequests/', 
        views.RequestsListView.as_view(),
        name='allrequests',
    ),
    path(
        'request-reject/<int:pk>/', 
        views.reject_request,
        name='reject_request',
    ),
    path(
        'request-accept/<int:pk>/', 
        views.accept_request,
        name='accept_request',
    ),
    path(
        'request-delete/<int:pk>/', 
        views.delete_request,
        name='delete_request',
    ),
    path(
        'report/', 
        views.ReportView.as_view(),
        name='report',
    ),

]