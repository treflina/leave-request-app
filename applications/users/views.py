from datetime import date, datetime
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django import forms

from django.views.generic import (
    View,
    TemplateView,
    CreateView,
    ListView,
    UpdateView,
)

from django.views.generic.edit import (
    FormView,
)

from applications.users.mixins import TopManagerPermisoMixin

from .forms import (
    UserRegisterForm,
    LoginForm,
    UpdatePasswordForm,
)
#
from .models import User

from applications.requests.models import Request
from applications.sickleaves.models import Sickleave


class UserRegisterView(TopManagerPermisoMixin, FormView):
    """Employee register form page."""

    template_name = 'users/register.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('users_app:user-register')
    login_url = reverse_lazy('users_app:user-login')

    def form_valid(self, form):
        # employee = form.save()
        User.objects.create_user(
            form.cleaned_data['username'],
            form.cleaned_data['password1'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            position=form.cleaned_data['position'],
            role=form.cleaned_data['role'],
            email=form.cleaned_data['email'],
            work_email=form.cleaned_data['work_email'],
            position_addinfo=form.cleaned_data['position_addinfo'],
            workplace=form.cleaned_data['workplace'],
            manager=form.cleaned_data['manager'],
            working_hours=form.cleaned_data['working_hours'],
            annual_leave=form.cleaned_data['annual_leave'],
            current_leave=form.cleaned_data['current_leave'],
            contract_end=form.cleaned_data['contract_end'],
            additional_info=form.cleaned_data['additional_info'],
        )

        return super(UserRegisterView, self).form_valid(form)


class LoginUser(FormView):
    """User login page"""

    template_name = 'users/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('home_app:index')

    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )

        login(self.request, user)
        return super(LoginUser, self).form_valid(form)


class LogoutView(View):

    def get(self, request, *args, **kargs):
        logout(request)
        return HttpResponseRedirect(
            reverse(
                'users_app:user-login'
            )
        )


@login_required(login_url='users_app:user-login')
def update_password(request):
    form = UpdatePasswordForm()
    person = request.user
    if request.method == 'POST':
        form = UpdatePasswordForm(request.POST)
        new_password = request.POST['password2']
        user = authenticate(
            username=person.username,
            password=request.POST['password1']
        )
        if user:
            if request.POST['password3'] != new_password:
                messages.error(request, 'Niepoprawnie powtórzono nowe hasło.')
            else:
                user = request.user
                user.set_password(new_password)
                user.save()
                logout(request)
                return HttpResponseRedirect(
                    reverse(
                        'users_app:user-login'
                    )
                )
        else:
            messages.error(request, 'Niepoprawnie podano dotychczasowe hasło.')
    return render(request, 'users/update_password.html', {'form': form})


class AllEmployeesList(TopManagerPermisoMixin, ListView):
    """Employees listing page for head/manager"""

    template_name = "users/all_employees.html"
    model = User
    context_object_name = 'employees'
    login_url = reverse_lazy('users_app:user-login')

    def get_context_data(self, **kwargs):

        context = super(AllEmployeesList, self).get_context_data(**kwargs)
        all_employees = User.objects.filter(
            is_active=True).exclude(username="admin")
        today = date.today()

        for employee in all_employees:
            if employee.working_hours == 1.00:
                employee.working_hours = 1
            today_sick = Sickleave.objects.filter(Q(start_date__lte=today) & Q(
                end_date__gte=today) & Q(employee__id=employee.id)).all()
            today_requests = Request.objects.filter(Q(start_date__lte=today) & Q(
                end_date__gte=today) & Q(author__id=employee.id)).exclude(status="odrzucony").all()
            if ("rodz" or "wych" or "mac" or "rehab" or "urlop" or "bezpł") in employee.additional_info:
                employee.today_note = ""
            elif len(today_sick) > 0:
                if today_sick[0].type == "O":
                    employee.today_note = "O"
                elif today_sick[0].type == "K":
                    employee.today_note = "K"
                elif today_sick[0].type == "I":
                    employee.today_note = "I"
                else:
                    employee.today_note = "C"
            elif len(today_requests) != 0:
                list_req = [tr.type for tr in today_requests]
                employee.today_note = list_req[0]
            else:
                employee.today_note = "✓"

        context['all_employees'] = all_employees
        return context


class AdminEmployeesList(TopManagerPermisoMixin, ListView):
    """Employees listing page for admin"""

    template_name = "users/admin_all_employees.html"
    model = User
    context_object_name = 'employees'
    login_url = reverse_lazy('users_app:user-login')

    def get_context_data(self, **kwargs):

        context = super(AdminEmployeesList, self).get_context_data(**kwargs)
        employees = User.objects.order_by(
            '-is_active', 'last_name', 'first_name').all()

        for employee in employees:
            if employee.working_hours == 1.00:
                employee.working_hours = 1
            if employee.role == "P":
                employee.is_manager = "NIE"
            else:
                employee.is_manager = "TAK"

        context['employees'] = employees
        return context


class EmployeeUpdateView(TopManagerPermisoMixin, UpdateView):
    """Employee details update form."""

    model = User
    template_name = "users/update_employee.html"
    login_url = reverse_lazy('users_app:user-login')

    fields = ['username', 'email', 'work_email', 'first_name', 'last_name', 'position', 'position_addinfo',
              'workplace', 'role', 'manager', 'working_hours', 'annual_leave', 'current_leave', 'contract_end', 'is_active', 'is_staff',
              'additional_info', ]

    success_url = reverse_lazy('users_app:admin-all-employees')

    def get_context_data(self, **kwargs):
        context = super(EmployeeUpdateView, self).get_context_data(**kwargs)
        context['form'].fields['manager'].queryset = User.objects.filter(
            ~Q(role="P") & Q(is_active=True)).order_by('last_name')
        return context


@login_required(login_url='users_app:user-login')
def delete_employee(request, pk):
    employee_to_delete = User.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse('users_app:admin-all-employees'))
