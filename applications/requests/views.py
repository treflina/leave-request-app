from io import BytesIO

from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import HttpResponseRedirect, FileResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from applications.users.mixins import TopManagerPermisoMixin
from django.views.generic import FormView, ListView

from pdf_creator import create_pdf
from wnioski.settings import get_secret

from applications.users.models import User
from applications.sickleaves.models import Sickleave
from .forms import RequestForm, ReportForm
from .managers import RequestManager
from .models import Request


class RequestFormView(LoginRequiredMixin, FormView):

    form_class = RequestForm
    template_name = 'requests/send_request.html'
    success_url = '.'
    login_url = reverse_lazy('users_app:user-login')

    def get_context_data(self, **kwargs):

        context = super(RequestFormView, self).get_context_data(**kwargs)
        context['form'].fields['send_to_person'].queryset = User.objects.filter((Q(id=self.request.user.manager_id)|Q(role='S')|Q(role='T'))&Q(is_active=True)).exclude(id=self.request.user.id).order_by('-role')
        if self.request.user.working_hours < 1:
            context['part'] = True
        return context

    def form_valid(self, form):

        user = self.request.user
        type = form.cleaned_data['type']
        days = form.cleaned_data['days']
        if (type == 'WS' or type == 'WN' or type == 'DW') and days != None:
            if days > 0:
                days = 0
        if (type == 'WS' or type == 'WN' or type == 'DW') and days == None:
            days = 0
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        send_to_person = form.cleaned_data['send_to_person']

        request = Request(
            author=user,
            type=type,
            work_date=form.cleaned_data["work_date"],
            start_date=start_date,
            end_date=end_date,
            days=days,
            substitute=form.cleaned_data['substitute'],
            send_to_person=send_to_person
        ).save()
        subject = f"{user} prosi o akceptację wniosku ({start_date}- {end_date})"
        message = f" {user} prosi o akceptację wniosku o wolne ({type}) w okresie {start_date} - {end_date}.\r\n \r\nZaopiniuj otrzymany wniosek. \r\n \r\nWiadomość wygenerowana automatycznie."
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [send_to_person.work_email],
            fail_silently=False,
        )
        user.current_leave -= days
        user.save(update_fields=['current_leave'])
        messages.success(self.request, 'Wniosek został pomyślnie złożony.')
        return super(RequestFormView, self).form_valid(form)


class UserRequestsListView(LoginRequiredMixin, ListView):

    template_name = "requests/user_requests.html"
    model = Request
    login_url = reverse_lazy('users_app:user-login')

    def get_context_data(self, **kwargs):

        context = super(UserRequestsListView, self).get_context_data(**kwargs)
        user = self.request.user
        context['user_requests_holiday'] = Request.objects.user_requests_holiday(
            user)
        context['user_requests_others'] = Request.objects.user_requests_others(
            user)
        return context


class RequestsListView(TopManagerPermisoMixin, ListView):

    template_name = "requests/allrequests.html"
    model = Request
    login_url = reverse_lazy('users_app:user-login')

    def get_context_data(self, **kwargs):

        context = super(RequestsListView, self).get_context_data(**kwargs)
        user = self.request.user
        context['requests_received'] = Request.objects.requests_to_accept(user)
        if len(context['requests_received']) == 0:
            context['no_request'] = True

        if user.role == "T" or user.role == "S" or user.is_staff:
            context['requests_holiday'] = Request.objects.requests_holiday_topmanager(
                user)
            context['requests_others'] = Request.objects.requests_others_topmanager(
                user)
        else:
            context['requests_holiday'] = Request.objects.requests_holiday(
                user)
            context['requests_others'] = Request.objects.requests_others(user)

        return context


def accept_request(request, pk):

    user = request.user
    request_to_accept = Request.objects.get(id=pk)
    request_to_accept.status = 'zaakceptowany'
    request_to_accept.signed_by = user.first_name+" "+user.last_name
    request_to_accept.save(update_fields=['status', 'signed_by'])
    return HttpResponseRedirect(reverse('requests_app:allrequests'))


def reject_request(request, pk):

    user = request.user
    request_to_reject = Request.objects.get(id=pk)
    if request_to_reject.type == 'W':
        employee_to_update = User.objects.get(id=request_to_reject.author.id)
        employee_to_update.current_leave += request_to_reject.days
        employee_to_update.save(update_fields=['current_leave'])
    request_to_reject.status = 'odrzucony'
    request_to_reject.signed_by = user.first_name+" "+user.last_name
    request_to_reject.save(update_fields=['status', 'signed_by'])

    return HttpResponseRedirect(reverse('requests_app:allrequests'))


def delete_request(request, pk):

    user = request.user
    request_to_delete = Request.objects.get(id=pk)
    if request_to_delete.type == 'W':
        user.current_leave += request_to_delete.days
        user.save(update_fields=['current_leave'])
    request_to_delete.delete()
    return HttpResponseRedirect(reverse('requests_app:user_requests'))


class ReportView(TopManagerPermisoMixin, FormView):

    form_class = ReportForm
    template_name = 'requests/report.html'
    success_url = '.'
    login_url = reverse_lazy('users_app:user-login')

    def form_valid(self, form):

        person = form.cleaned_data["person"]
        type = form.cleaned_data["type"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        pdf_buffer = BytesIO()

        urlop_data = [["Lp.", "Data złożenia", "Nazwisko i imię",
                       "Od", "Do", "Status", "Podpisany przez:"]]
        other_data = [
            ["Lp.", "Data złożenia", "Nazwisko i imię", "W dniu", "Rodzaj", "Za pracę dnia", "Status",
             "Podpisany przez:"]]
        c_data = [["Lp.", "Data wystawienia", "Nr dokumentu",
                   "Nazwisko i imię", "Rodzaj", "Od", "Do", "Inne"]]

        if type == "W":
            x = 1
            if person == "all_employees":
                requests_data = Request.objects.filter(Q(type='W') & Q(
                    start_date__gte=start_date) & Q(start_date__lte=end_date)).order_by('created').all()
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
            else:
                employee = User.objects.get(id=person)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                requests_data = Request.objects.filter(Q(type='W') & Q(author__id=employee.id) & Q(
                    start_date__gte=start_date) & Q(start_date__lte=end_date) & ~Q(status="oczekujący")).order_by('created').all()
            for item in requests_data:
                created_newformat = str(item.created).split()[0]
                employee_repr = item.author.last_name+" " + \
                    item.author.first_name+" "+item.author.position_addinfo
                data = [x, created_newformat, employee_repr, item.start_date,
                        item.end_date, item.status, item.signed_by]
                urlop_data.append(data)
                x = x + 1
            title = "Wnioski urlopowe"
            create_pdf(urlop_data, pdf_buffer, title,
                       start_date, end_date, name, position)
            pdf_buffer.seek(0)
            return FileResponse(pdf_buffer, as_attachment=True,
                                filename=f'wykaz urlopów {employee}.pdf')
        elif type == "WS":
            x = 1
            if person == "all_employees":
                requests_data = Request.objects.filter(~Q(type='W') & Q(
                    start_date__gte=start_date) & Q(start_date__lte=end_date)).order_by('created').all()
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
            else:
                employee = User.objects.get(id=person)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                requests_data = Request.objects.filter(~Q(type='W') & Q(author__id=employee.id) & Q(
                    start_date__gte=start_date) & Q(start_date__lte=end_date) & ~Q(status="oczekujący")).order_by('created').all()

            for item in requests_data:
                created_newformat = str(item.created).split()[0]
                employee_repr = item.author.last_name+" " + \
                    item.author.first_name+" "+item.author.position_addinfo
                data1 = [x, created_newformat, employee_repr, item.start_date,
                         item.type, item.work_date, item.status, item.signed_by]
                other_data.append(data1)
                x = x + 1

            title = "Wnioski o dni wolne za pracujące soboty (niedziele, święta)"
            create_pdf(other_data, pdf_buffer, title,
                       start_date, end_date, name, position)
            pdf_buffer.seek(0)
            return FileResponse(pdf_buffer, as_attachment=True,
                                filename=f'wykaz dni wolne {employee}.pdf')
        if type == "C":
            x = 1
            if person == "all_employees":
                sickleaves_data = Sickleave.objects.filter(Q(start_date__gte=start_date) & Q(
                    start_date__lte=end_date)).order_by('start_date').all()
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
            else:
                employee = User.objects.get(id=person)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                sickleaves_data = Sickleave.objects.filter(Q(employee__id=employee.id) & Q(
                    start_date__gte=start_date) & Q(start_date__lte=end_date)).order_by('start_date').all()
            for item in sickleaves_data:
                employee_repr = item.employee.last_name + " " + \
                    item.employee.first_name + " " + item.employee.position_addinfo
                data2 = [x, item.issue_date, item.doc_number, employee_repr,
                         item.type, item.start_date, item.end_date, item.additional_info]
                c_data.append(data2)
                x = x + 1
            title = "Zwolnienia lekarskie"
            create_pdf(c_data, pdf_buffer, title,
                       start_date, end_date, name, position)
            pdf_buffer.seek(0)
            return FileResponse(pdf_buffer, as_attachment=True,
                                filename=f'chorobowe {employee}.pdf')
