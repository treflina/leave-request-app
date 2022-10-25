from io import BytesIO
from distutils.log import error
from simple_history.utils import update_change_reason

from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import HttpResponseRedirect, FileResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, ListView, UpdateView

from pdf_creator import create_pdf
from wnioski.settings import get_secret

from applications.users.models import User
from applications.sickleaves.models import Sickleave
from applications.users.mixins import TopManagerPermisoMixin

from .forms import RequestForm, ReportForm, UpdateRequestForm
from .managers import RequestManager
from .models import Request


class RequestFormView(LoginRequiredMixin, FormView):
    """Leave request form."""

    form_class = RequestForm
    template_name = "requests/send_request.html"
    success_url = "."
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):

        context = super(RequestFormView, self).get_context_data(**kwargs)
        context["form"].fields["send_to_person"].queryset = (
            User.objects.filter(
                (Q(id=self.request.user.manager_id) | Q(role="S") | Q(role="T"))
                & Q(is_active=True)
            )
            .exclude(id=self.request.user.id)
            .order_by("role")
        )
        if self.request.user.working_hours < 1:
            context["part"] = True
        return context

    def form_valid(self, form):

        user = self.request.user
        type = form.cleaned_data["type"]
        days = form.cleaned_data["days"]
        if (type == "WS" or type == "WN" or type == "DW") and days != None:
            if days > 0:
                days = 0
        if (type == "WS" or type == "WN" or type == "DW") and days == None:
            days = 0
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        work_date = form.cleaned_data["work_date"]
        send_to_person = form.cleaned_data["send_to_person"]
        if (type == "WS" or type == "WN") and Request.objects.filter(
            Q(author=user) & Q(work_date=work_date) & ~Q(status="odrzucony")
        ).exists():
            messages.error(
                self.request,
                "Błąd. Wniosek o odebranie dnia wolnego za wskazaną pracującą sobotę/niedzielę już został złożony.",
            )
            return self.form_invalid(form)

        request = Request(
            author=user,
            type=type,
            work_date=work_date,
            start_date=start_date,
            end_date=end_date,
            days=days,
            substitute=form.cleaned_data["substitute"],
            send_to_person=send_to_person,
        ).save()
        start_date = start_date.strftime("%d.%m.%y")
        end_date = end_date.strftime("%d.%m.%y")
        if work_date:
            work_date = work_date.strftime("%d.%m.%y")
        if type == "W" and start_date == end_date:
            text_msg = f"urlop wypoczynkowy w dniu {start_date}"
        elif type == "W":
            text_msg = f"urlop wypoczynkowy w okresie {start_date} - {end_date}"
        elif type == "WS" or type == "WN":
            text_msg = f"dzień wolny ({type}) {start_date} za pracę {work_date}"
        elif type == "DW":
            text_msg = f"dzień wolny {start_date} za święto przypadające w sobotę"
        else:
            text_msg = f"wolne ({type}) w okresie {start_date} - {end_date}"

        subject = f"{user} prosi o akceptację wniosku ({start_date}-{end_date})"
        message = f"{user} prosi o akceptację wniosku o {text_msg}.\r\n \r\nZaopiniuj otrzymany wniosek na: https://pracownik.mbp.opole.pl/. \r\n \r\nWiadomość wygenerowana automatycznie."
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [send_to_person.work_email],
            fail_silently=False,
        )
        user.current_leave -= days
        user.save(update_fields=["current_leave"])
        messages.success(self.request, "Wniosek został pomyślnie złożony.")
        return super(RequestFormView, self).form_valid(form)

    def form_invalid(self, form):
        print("sth went wrong")
        for key, value in self.request.POST.items():
            print('Key: %s' % (key) )
    # print(f'Key: {key}') in Python >= 3.7
            print('Value %s' % (value) )
        return super(RequestFormView, self).form_invalid(form)


class RequestChangeView(TopManagerPermisoMixin, UpdateView):
    """Change request form for HR."""

    model = Request
    form_class = UpdateRequestForm
    template_name = "requests/changerequest.html"
    login_url = reverse_lazy("users_app:user-login")
    success_url = reverse_lazy("requests_app:hrallrequests")

    def get_context_data(self, **kwargs):
        context = super(RequestChangeView, self).get_context_data(**kwargs)
        context["form"].fields["send_to_person"].queryset = User.objects.filter(
            (Q(id=self.request.user.manager_id) | Q(role="S") | Q(role="T"))
            & Q(is_active=True)
        ).order_by("role")

        if self.object.author.working_hours < 1:
            context["part"] = True

        history_changereason = (
            Request.history.filter(id=self.object.id).first().history_change_reason
        )
        if history_changereason in ["None", ""] or history_changereason is None:
            context["history_changereason"] = "brak"
        else:
            context["history_changereason"] = history_changereason
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        req = self.get_object()
        changeReason = form.cleaned_data.get("history_change_reason")
        update_change_reason(req, changeReason)
        return response


class UserRequestsListView(LoginRequiredMixin, ListView):
    """Employee requests listing page."""

    template_name = "requests/user_requests.html"
    model = Request
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):

        context = super(UserRequestsListView, self).get_context_data(**kwargs)
        user = self.request.user
        context["user_requests_holiday"] = Request.objects.user_requests_holiday(user)
        context["user_requests_other"] = Request.objects.user_requests_other(user)
        return context


class RequestsListView(TopManagerPermisoMixin, ListView):
    """All employees 30 latest requests (except those sent by current user themselves) sent from the beginning of the year and for the next 3 weeks."""

    model = Request
    template_name = "requests/allrequests.html"
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):

        context = super(RequestsListView, self).get_context_data(**kwargs)
        user = self.request.user
        context["requests_received"] = Request.objects.requests_to_accept(user)
        if len(context["requests_received"]) == 0:
            context["no_request"] = True

        if user.role == "T" or user.role == "S" or user.is_staff:
            context["requests_holiday"] = Request.objects.requests_holiday_topmanager(
                user
            )[:30]
            context["requests_other"] = Request.objects.requests_other_topmanager(user)[
                :30
            ]

            if len(context["requests_other"]) < len(
                Request.objects.allrequests_other_topmanager(user).all()
            ):
                context["showall_other"] = True
            if len(context["requests_holiday"]) < len(
                Request.objects.allrequests_holiday_topmanager(user).all()
            ):
                context["showall_holiday"] = True

        else:
            context["requests_holiday"] = Request.objects.requests_holiday(user)[:30]
            context["requests_other"] = Request.objects.requests_other(user)[:30]
            if len(context["requests_holiday"]) < len(
                Request.objects.allrequests_holiday(user).all()
            ):
                context["showall_holiday"] = True
            if len(context["requests_other"]) < len(
                Request.objects.allrequests_other(user).all()
            ):
                context["showall_other"] = True

        return context


class HRAllRequestsListView(TopManagerPermisoMixin, ListView):
    """All employees requests listing page for HR department. It contains all requests except those sent by current user themselves."""

    model = Request
    template_name = "requests/hrallrequests.html"
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):

        context = super(HRAllRequestsListView, self).get_context_data(**kwargs)
        context["requests_holiday"] = Request.objects.hrallrequests_holiday()
        context["requests_other"] = Request.objects.hrallrequests_other()
        return context


class AllHolidayRequestsListView(TopManagerPermisoMixin, ListView):
    """All holiday employees requests listing page. It contains all requests except those sent by current user themselves."""

    model = Request
    template_name = "requests/holiday-allrequests.html"
    login_url = reverse_lazy("users_app:user-login")
    context_object_name = "requests_holiday"

    def get_queryset(self):
        user = self.request.user
        if user.role == "T" or user.role == "S" or user.is_staff:
            return Request.objects.allrequests_holiday_topmanager(user)
        else:
            return Request.objects.allrequests_holiday(user)


class AllOtherRequestsListView(TopManagerPermisoMixin, ListView):
    """All other employees requests listing page. It contains all requests except those sent by current user themselves."""

    model = Request
    template_name = "requests/other-allrequests.html"
    login_url = reverse_lazy("users_app:user-login")
    context_object_name = "requests_other"

    def get_queryset(self):
        user = self.request.user
        if user.role == "T" or user.role == "S" or user.is_staff:
            return Request.objects.allrequests_other_topmanager(user)
        else:
            return Request.objects.allrequests_other(user)


def accept_request(request, pk):
    """Accepts the employee request."""
    user = request.user
    request_to_accept = Request.objects.get(id=pk)
    request_to_accept.status = "zaakceptowany"
    request_to_accept.signed_by = user.first_name + " " + user.last_name
    request_to_accept.save(update_fields=["status", "signed_by"])
    return HttpResponseRedirect(reverse("requests_app:allrequests"))


def reject_request(request, pk):
    """Rejects the employee request."""
    user = request.user
    request_to_reject = Request.objects.get(id=pk)
    if request_to_reject.type == "W":
        employee_to_update = User.objects.get(id=request_to_reject.author.id)
        employee_to_update.current_leave += request_to_reject.days
        employee_to_update.save(update_fields=["current_leave"])
    request_to_reject.status = "odrzucony"
    request_to_reject.signed_by = user.first_name + " " + user.last_name
    request_to_reject.save(update_fields=["status", "signed_by"])

    return HttpResponseRedirect(reverse("requests_app:allrequests"))


def delete_request(request, pk):
    """Withdraws the request."""
    user = request.user
    request_to_delete = Request.objects.get(id=pk)
    if request_to_delete.type == "W":
        user.current_leave += request_to_delete.days
        user.save(update_fields=["current_leave"])
    request_to_delete.delete()
    return HttpResponseRedirect(reverse("requests_app:user_requests"))


class ReportView(TopManagerPermisoMixin, FormView):
    """Creates pdf report about requests and sickleaves for a chosen time period."""

    form_class = ReportForm
    template_name = "requests/report.html"
    success_url = "."
    login_url = reverse_lazy("users_app:user-login")

    def form_valid(self, form):

        person = form.cleaned_data["person"]
        type = form.cleaned_data["type"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        pdf_buffer = BytesIO()

        urlop_data = [
            [
                "Lp.",
                "Data złożenia",
                "Nazwisko i imię",
                "Od",
                "Do",
                "Dni/godz.",
                "Status",
                "Podpisany przez:",
            ]
        ]
        other_data = [
            [
                "Lp.",
                "Data złożenia",
                "Nazwisko i imię",
                "W dniu",
                "Rodzaj",
                "Za pracę dnia",
                "Status",
                "Podpisany przez:",
            ]
        ]
        c_data = [
            [
                "Lp.",
                "Data wystawienia",
                "Nr dokumentu",
                "Nazwisko i imię",
                "Rodzaj",
                "Od",
                "Do",
                "Inne",
            ]
        ]

        if type == "W":
            x = 1
            if person == "all_employees":
                requests_data = (
                    Request.objects.filter(
                        Q(type="W")
                        & Q(start_date__gte=start_date)
                        & Q(start_date__lte=end_date)
                    )
                    .order_by("author")
                    .all()
                )
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
            else:
                employee = User.objects.get(id=person)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                requests_data = (
                    Request.objects.filter(
                        Q(type="W")
                        & Q(author__id=employee.id)
                        & Q(start_date__gte=start_date)
                        & Q(start_date__lte=end_date)
                        & ~Q(status="oczekujący")
                    )
                    .order_by("created")
                    .all()
                )
            for item in requests_data:
                created_newformat = str(item.created).split()[0]
                employee_repr = (
                    item.author.last_name
                    + " "
                    + item.author.first_name
                    + " "
                    + item.author.position_addinfo
                )
                data = [
                    x,
                    created_newformat,
                    employee_repr,
                    item.start_date,
                    item.end_date,
                    item.days,
                    item.status,
                    item.signed_by,
                ]
                urlop_data.append(data)
                x += 1
            title = "Wnioski urlopowe"
            create_pdf(
                urlop_data, pdf_buffer, title, start_date, end_date, name, position
            )
            pdf_buffer.seek(0)
            return FileResponse(
                pdf_buffer, as_attachment=True, filename=f"wykaz urlopów {employee}.pdf"
            )
        elif type == "WS":
            x = 1
            if person == "all_employees":
                requests_data = (
                    Request.objects.filter(
                        ~Q(type="W")
                        & Q(start_date__gte=start_date)
                        & Q(start_date__lte=end_date)
                    )
                    .order_by("author")
                    .all()
                )
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
            else:
                employee = User.objects.get(id=person)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                requests_data = (
                    Request.objects.filter(
                        ~Q(type="W")
                        & Q(author__id=employee.id)
                        & Q(start_date__gte=start_date)
                        & Q(start_date__lte=end_date)
                        & ~Q(status="oczekujący")
                    )
                    .order_by("created")
                    .all()
                )

            for item in requests_data:
                created_newformat = str(item.created).split()[0]
                employee_repr = (
                    item.author.last_name
                    + " "
                    + item.author.first_name
                    + " "
                    + item.author.position_addinfo
                )
                data1 = [
                    x,
                    created_newformat,
                    employee_repr,
                    item.start_date,
                    item.type,
                    item.work_date,
                    item.status,
                    item.signed_by,
                ]
                other_data.append(data1)
                x += 1

            title = "Wnioski o dni wolne za pracujące soboty (niedziele, święta)"
            create_pdf(
                other_data, pdf_buffer, title, start_date, end_date, name, position
            )
            pdf_buffer.seek(0)
            return FileResponse(
                pdf_buffer,
                as_attachment=True,
                filename=f"wykaz dni wolne {employee}.pdf",
            )
        if type == "C":
            x = 1
            if person == "all_employees":
                sickleaves_data = (
                    Sickleave.objects.filter(
                        Q(start_date__gte=start_date) & Q(start_date__lte=end_date)
                    )
                    .order_by("employee__last_name", "start_date")
                    .all()
                )
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
            else:
                employee = User.objects.get(id=person)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                sickleaves_data = (
                    Sickleave.objects.filter(
                        Q(employee__id=employee.id)
                        & Q(start_date__gte=start_date)
                        & Q(start_date__lte=end_date)
                    )
                    .order_by("start_date")
                    .all()
                )
            for item in sickleaves_data:
                employee_repr = (
                    item.employee.last_name
                    + " "
                    + item.employee.first_name
                    + " "
                    + item.employee.position_addinfo
                )
                data2 = [
                    x,
                    item.issue_date,
                    item.doc_number,
                    employee_repr,
                    item.type,
                    item.start_date,
                    item.end_date,
                    item.additional_info,
                ]
                c_data.append(data2)
                x += 1
            title = "Zwolnienia lekarskie"
            create_pdf(c_data, pdf_buffer, title, start_date, end_date, name, position)
            pdf_buffer.seek(0)
            return FileResponse(
                pdf_buffer, as_attachment=True, filename=f"chorobowe {employee}.pdf"
            )
