import django_filters
import operator
from functools import reduce
from datetime import date
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import (
    View,
    ListView,
    UpdateView,
)
from django.views.generic.edit import (
    FormView,
)
from django.forms.widgets import TextInput

from .forms import (
    UserRegisterForm,
    LoginForm,
    UpdatePasswordForm,
)
from .models import User
from applications.requests.models import Request
from applications.sickleaves.models import Sickleave
from applications.users.mixins import TopManagerPermisoMixin


class UserRegisterView(TopManagerPermisoMixin, FormView):
    """Employee register form page."""

    template_name = "users/register.html"
    form_class = UserRegisterForm
    success_url = reverse_lazy("users_app:admin-all-employees")
    login_url = reverse_lazy("users_app:user-login")

    def form_valid(self, form):
        User.objects.create_user(
            form.cleaned_data["username"],
            form.cleaned_data["password1"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            position=form.cleaned_data["position"],
            role=form.cleaned_data["role"],
            email=form.cleaned_data["email"],
            work_email=form.cleaned_data["work_email"],
            position_addinfo=form.cleaned_data["position_addinfo"],
            workplace=form.cleaned_data["workplace"],
            manager=form.cleaned_data["manager"],
            working_hours=form.cleaned_data["working_hours"],
            annual_leave=form.cleaned_data["annual_leave"],
            current_leave=form.cleaned_data["current_leave"],
            contract_end=form.cleaned_data["contract_end"],
            additional_info=form.cleaned_data["additional_info"],
        )

        return super(UserRegisterView, self).form_valid(form)


class LoginUser(FormView):
    """User login page"""

    template_name = "users/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("home_app:index")

    def form_valid(self, form):
        user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        login(self.request, user)
        return super(LoginUser, self).form_valid(form)


class LogoutView(View):
    def get(self, request, *args, **kargs):
        logout(request)
        return HttpResponseRedirect(reverse("users_app:user-login"))


@login_required(login_url="users_app:user-login")
def update_password(request):
    form = UpdatePasswordForm()
    person = request.user
    if request.method == "POST":
        form = UpdatePasswordForm(request.POST)
        new_password = request.POST["password2"]
        user = authenticate(
            username=person.username, password=request.POST["password1"]
        )
        if user:
            if request.POST["password3"] != new_password:
                messages.error(request, "Niepoprawnie powtórzono nowe hasło.")
            else:
                user = request.user
                user.set_password(new_password)
                user.save()
                logout(request)
                return HttpResponseRedirect(reverse("users_app:user-login"))
        else:
            messages.error(request, "Niepoprawnie podano dotychczasowe hasło.")
    return render(request, "users/update_password.html", {"form": form})


class UsersFilter(django_filters.FilterSet):
    """Filter used to search data in employees listing views."""

    lookup_fields = django_filters.CharFilter(
        method="filter_fields",
        label="Wyszukaj",
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Wyszukaj..."}),
    )

    class Meta:
        model = User
        fields = [
            "lookup_fields",
        ]

    @staticmethod
    def filter_fields(qs, name, value):
        query_words = value.split()
        return qs.filter(
            reduce(
                operator.and_,
                (
                    Q(first_name__icontains=word) | Q(last_name__icontains=word)
                    for word in query_words
                ),
            )
            | Q(position__icontains=value)
            | Q(workplace__icontains=value)
            | Q(additional_info__icontains=value)
        )


class AllEmployeesList(TopManagerPermisoMixin, ListView):
    """Employees listing view for head/manager with notification
    if an employee should be present at work today."""

    template_name = "users/all_employees.html"
    model = User
    context_object_name = "all_employees"
    login_url = reverse_lazy("users_app:user-login")

    def get_queryset(self, **kwargs):
        queryset = User.objects.filter(is_active=True).exclude(username="admin")
        filter = UsersFilter(self.request.GET, queryset)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_employees = self.get_queryset()
        today = date.today()
        for employee in all_employees:
            if employee.working_hours == 1.00:
                employee.working_hours = 1
            today_sick = Sickleave.objects.filter(
                Q(start_date__lte=today)
                & Q(end_date__gte=today)
                & Q(employee__id=employee.id)
            ).last()
            today_request = Request.objects.filter(
                Q(start_date__lte=today)
                & Q(end_date__gte=today)
                & Q(author__id=employee.id)
                & Q(status="zaakceptowany")
            ).last()
            if today_sick:
                employee.today_note = today_sick.leave_type
            elif today_request:
                employee.today_note = today_request.leave_type
            else:
                employee.today_note = "✓"

            long_absence_list_keywords = [
                "wych",
                "rodz",
                "mac",
                "rehab",
                "urlop",
                "bezpł",
            ]
            for info in long_absence_list_keywords:
                if info in employee.additional_info:
                    employee.today_note = ""

        context["all_employees"] = all_employees

        filterset = UsersFilter(self.request.GET, all_employees)
        context["filterset"] = filterset
        return context


class AdminEmployeesList(TopManagerPermisoMixin, ListView):
    """Employees listing view for HR with information about how many days off they are
    entitled to, how many duvet days have been taken in the current year.
    This view contains also a list of ex-employees"""

    template_name = "users/admin_all_employees.html"
    model = User
    context_object_name = "employees"
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):
        context = super(AdminEmployeesList, self).get_context_data(**kwargs)
        employees = User.objects.filter(is_active=True).order_by(
            "-is_active", "last_name", "first_name"
        )
        current_year = date.today().year

        for employee in employees:
            if employee.working_hours == 1.00:
                employee.working_hours = 1
            if employee.role == "P":
                employee.is_manager = "NIE"
            else:
                employee.is_manager = "TAK"

            employee.duvet_days_count = Request.objects.filter(
                author_id=employee.id,
                duvet_day=True,
                start_date__gte=date(current_year, 1, 1),
                start_date__lte=date(current_year, 12, 31),
            ).count()
        context["employees"] = employees

        exemployees = User.objects.filter(is_active=False).order_by(
            "last_name", "first_name"
        )
        context["exemployees"] = exemployees
        return context


class EmployeeUpdateView(TopManagerPermisoMixin, UpdateView):
    """Employee details update form."""

    model = User
    template_name = "users/update_employee.html"
    login_url = reverse_lazy("users_app:user-login")
    success_url = reverse_lazy("users_app:admin-all-employees")

    fields = [
        "username",
        "email",
        "work_email",
        "first_name",
        "last_name",
        "position",
        "position_addinfo",
        "workplace",
        "role",
        "manager",
        "working_hours",
        "annual_leave",
        "current_leave",
        "contract_end",
        "is_active",
        "is_staff",
        "additional_info",
    ]

    def get_context_data(self, **kwargs):
        context = super(EmployeeUpdateView, self).get_context_data(**kwargs)
        context["form"].fields["manager"].queryset = User.objects.filter(
            ~Q(role="P") & Q(is_active=True)
        ).order_by("last_name")
        return context


@login_required(login_url="users_app:user-login")
def delete_employee(request, pk):
    User.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse("users_app:admin-all-employees"))


@login_required(login_url="users_app:user-login")
def add_annual_leave(request):
    """Tool to add at the beginning of the year all employees annual leave entitlement
    to their current leave entitlement."""
    for employee in User.objects.filter(is_active=True):
        employee.current_leave += employee.annual_leave
        employee.save()
    return HttpResponseRedirect(reverse("users_app:admin-all-employees"))
