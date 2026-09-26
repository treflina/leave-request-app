from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    UpdateView,
    ListView
)

from .forms import MessageForm
from .models import Message



class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "inbox/message_list.html"
    context_object_name = "messages"
    ordering = ["-id"]


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "inbox/message_form.html"
    success_url = reverse_lazy("inbox_app:message_list")


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "inbox/message_form.html"
    success_url = reverse_lazy("inbox_app:message_list")


class MessageRecipientsView(DetailView):
    model = Message
    template_name = "inbox/message_recipients.html"
    context_object_name = "message"

    def get_queryset(self):
        return Message.objects.prefetch_related("employees")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        employee_ids = request.POST.getlist("remove_employees")

        if employee_ids:
            self.object.employees.remove(*employee_ids)

            count = len(employee_ids)

            messages.success(
                request,
                f"Usunięto {count} "
                f"{'pracownika' if count == 1 else 'pracowników'} "
                f"z odbiorców wiadomości.",
            )

        return redirect(
            "inbox_app:message_recipients",
            pk=self.object.pk,
        )
