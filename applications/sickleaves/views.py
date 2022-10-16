from datetime import datetime
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

    context_object_name = "sickleaves"
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy("users_app:user-login")

    def get_queryset(self):
        return Sickleave.objects.all().order_by("-issue_date")


class SickleaveCreateView(TopManagerPermisoMixin, CreateView):
    """Sick leave registration form."""

    template_name = "sickleaves/add_sickleave.html"
    model = Sickleave
    form_class = SickleaveForm
    success_url = reverse_lazy("sickleaves_app:sickleaves")
    login_url = reverse_lazy("users_app:user-login")

    def form_valid(self, form):
        employee = form.cleaned_data["employee"]
        start_date = form.cleaned_data["start_date"]
        start_date = start_date.strftime("%d.%m.%y")
        end_date = form.cleaned_data["end_date"]
        end_date = end_date.strftime("%d.%m.%y")
        type = form.cleaned_data["type"]
        head = form.cleaned_data["head"]
        manager = form.cleaned_data["manager"]
        instructor = form.cleaned_data["instructor"]
        text_info = ""
        if type == "O":
            text = "na opiece nad chorym członkiem rodziny"
            text_subj = f"opieka"
        elif type == "K":
            text = "na kwarantannie"
            text_subj = f"kwarantanna"
            text_info = f"Podane daty mogą ulec zmianie."
        elif type == "I":
            text = "na izolacji"
            text_subj = f"izolacja"
        else:
            text = f"na zwolnieniu lekarskim ({type})"
            text_subj = f"chorobowe"

        subject = f"{text_subj} {employee.first_name} {employee.last_name} ({start_date} - {end_date})"
        message = f"Dzień dobry,\r\n{employee.first_name} {employee.last_name} przebywa {text} w dniach {start_date} do {end_date}. {text_info}\r\n \r\nWiadomość wygenerowana automatycznie."
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
        if employee.manager:
            send_to_people = []
            if head:
                person = User.objects.filter(Q(role="S")).first()
                send_to_people.append(person.work_email)
            if manager:
                person = User.objects.filter(Q(id=employee.manager.id)).first()
                send_to_people.append(person.work_email)
            if instructor:
                person = User.objects.filter(
                    Q(position="starszy kustosz - instruktor")
                ).first()
                send_to_people.append(person.work_email)
            # send_to_people = User.objects.filter(
            #     Q(role='S') | Q(id=employee.manager.id) | Q(position="starszy kustosz - instruktor")).distinct()
            send_to_people_list = [p for p in set(send_to_people)] + [EMAIL_HOST_USER]

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
    success_url = reverse_lazy("sickleaves_app:sickleaves")
    login_url = reverse_lazy("users_app:user-login")


def delete_sickleave(request, pk):
    """Deletes sick leave."""
    sickleave_to_delete = Sickleave.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))
