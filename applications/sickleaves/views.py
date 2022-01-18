from django.shortcuts import render
from django.urls import path, reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.query_utils import Q

from applications.users.mixins import TopManagerPermisoMixin
from applications.users.models import User
from wnioski.settings import get_secret
from .models import Sickleave
from .forms import SickleaveForm


class SickleavesListView(TopManagerPermisoMixin, ListView):
    """Sick leaves listing page."""

    context_object_name = 'sickleaves'
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy('users_app:user-login')

    def get_queryset(self):
        return Sickleave.objects.all().order_by('-issue_date')


class SickleaveCreateView(TopManagerPermisoMixin, CreateView):
    """Sick leave registration form."""

    template_name = "sickleaves/add_sickleave.html"
    model = Sickleave
    form_class = SickleaveForm
    success_url = reverse_lazy('sickleaves_app:sickleaves')
    login_url = reverse_lazy('users_app:user-login')

    def form_valid(self, form):
        employee = form.cleaned_data["employee"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        type = form.cleaned_data["type"]

        subject = f"chorobowe {employee.first_name} {employee.last_name} ({start_date} - {end_date})"
        message = f"Dzień dobry,\r\n {employee.first_name} {employee.last_name} przebywa na zwolnieniu lekarskim ({type}) w dniach {start_date} - {end_date}.\r\n \r\nWiadomość wygenerowana automatycznie."
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
        if employee.manager:
            send_to_people = User.objects.filter(
                Q(role='S') | Q(id=employee.manager.id) | Q(position="starszy kustosz - instruktor")).distinct()
            send_to_people_list = [
                person.work_email for person in send_to_people] + [EMAIL_HOST_USER]

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                send_to_people_list,
                fail_silently=False,
            )

        return super(SickleaveCreateView, self).form_valid(form)


class SickleaveUpdateView(TopManagerPermisoMixin, UpdateView):
    """Registered sick leave update form."""
    model = Sickleave
    template_name = "sickleaves/update_sickleave.html"
    fields = "__all__"
    success_url = reverse_lazy('sickleaves_app:sickleaves')
    login_url = reverse_lazy('users_app:user-login')


def delete_sickleave(request, pk):
    """Deletes sick leave."""
    sickleave_to_delete = Sickleave.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse('sickleaves_app:sickleaves'))
