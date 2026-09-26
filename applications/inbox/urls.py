from django.urls import path

from .views import (
    MessageCreateView,
    MessageListView,
    MessageRecipientsView,
    MessageUpdateView,
)

app_name = "inbox_app"


urlpatterns = [
    path(
        "wiadomosci/lista",
        MessageListView.as_view(),
        name="message_list",
    ),
    path(
        "wiadomosci/nowa/",
        MessageCreateView.as_view(),
        name="message_create",
    ),

    path(
        "wiadomosci/<int:pk>/edytuj/",
        MessageUpdateView.as_view(),
        name="message_update",
    ),
    path(
        "wiadomosci/<int:pk>/odbiorcy/",
        MessageRecipientsView.as_view(),
        name="message_recipients",
    ),
]
