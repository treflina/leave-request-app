import django_filters
import logging
import operator
import json
from functools import reduce
from datetime import date
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.http import require_POST
from django.views.generic import (
    View,
    ListView,
    UpdateView,
)
from django.views.generic.edit import (
    FormView,
)
from django.forms.widgets import TextInput
from two_factor.views import LoginView as TwoFactorLoginView

from .forms import (
    UserRegisterForm,
    LoginForm,
    UpdatePasswordForm,
)
from .models import User
from webpush.models import PushInformation
from applications.requests.models import Request
from applications.sickleaves.models import Sickleave
from applications.users.mixins import (
    StaffAndDirectorPermissionMixin,
    check_staff
)

logger = logging.getLogger("django")


class UserRegisterView(StaffAndDirectorPermissionMixin, FormView):
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


class LoginUser(TwoFactorLoginView):
    """User login page"""

    template_name = "two_factor/core/login.html"


class LogoutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse("users_app:user-login"))


@login_required(login_url="users_app:user-login")
def update_password(request):
    person = request.user
    if request.method == "POST":
        form = UpdatePasswordForm(user=person, data=request.POST)
        if form.is_valid():
            if authenticate(
                username=person.username,
                password=form.cleaned_data["password1"],
            ):
                person.set_password(form.cleaned_data["password2"])
                person.save()
                logout(request)
                return HttpResponseRedirect(reverse("users_app:user-login"))
            messages.error(request, "Niepoprawnie podano dotychczasowe hasło.")
    else:
        form = UpdatePasswordForm(user=person)
    return render(request, "users/update_password.html", {"form": form})


class UsersFilter(django_filters.FilterSet):
    """Filter used to search data in employees listing views."""

    lookup_fields = django_filters.CharFilter(
        method="filter_fields",
        label="Wyszukaj",
        widget=TextInput
        (attrs={"class": "form-control", "placeholder": "Wyszukaj..."}
         ),
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
                    Q(first_name__icontains=word)
                    | Q(last_name__icontains=word)
                    for word in query_words
                ),
            )
            | Q(position__icontains=value)
            | Q(workplace__icontains=value)
            | Q(additional_info__icontains=value)
        )


class AllEmployeesList(StaffAndDirectorPermissionMixin, ListView):
    """Employees listing view for head/manager with notification
    if an employee should be present at work today."""

    template_name = "users/all_employees.html"
    model = User
    context_object_name = "all_employees"
    login_url = reverse_lazy("users_app:user-login")

    def get_queryset(self, **kwargs):
        queryset = User.objects.filter(
            is_active=True
            ).exclude(
                username="hr_service"
                )
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


class AdminEmployeesList(StaffAndDirectorPermissionMixin, ListView):
    """Active employee management list for HR."""

    template_name = "users/admin_all_employees.html"
    model = User
    context_object_name = "employees"
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):
        context = super(AdminEmployeesList, self).get_context_data(**kwargs)
        employees = User.objects.filter(is_active=True).exclude(
            username="hr_service").order_by(
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

        return context


class FormerEmployeesList(StaffAndDirectorPermissionMixin, ListView):
    """Former employee management list for HR."""

    template_name = "users/former_employees.html"
    model = User
    context_object_name = "employees"
    login_url = reverse_lazy("users_app:user-login")

    def get_queryset(self):
        return User.objects.filter(is_active=False).order_by("last_name", "first_name")


class EmployeeUpdateView(StaffAndDirectorPermissionMixin, UpdateView):
    """Employee details update form."""

    model = User
    template_name = "users/update_employee.html"
    login_url = reverse_lazy("users_app:user-login")

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
        "email_notifications"
    ]

    def get_success_url(self):
        from_param = self.request.GET.get("from") or self.request.POST.get("from")
        if from_param == "former":
            return reverse_lazy("users_app:former-employees")
        return reverse_lazy("users_app:admin-all-employees")

    def get_context_data(self, **kwargs):
        context = super(EmployeeUpdateView, self).get_context_data(**kwargs)
        context["back_url"] = self.get_success_url()
        context["form"].fields["manager"].queryset = User.objects.filter(
            ~Q(role="P") & Q(is_active=True)
        ).order_by("last_name")
        for field in context["form"].fields.values():
            if field.widget.input_type == "checkbox":
                field.widget.attrs["class"] = (
                    "h-4 w-4 rounded border-slate-300 text-[#28a745] "
                    "focus:ring-[#28a745]"
                )
            else:
                field.widget.attrs["class"] = (
                    "mt-1 w-full rounded-lg border border-slate-300 bg-slate-50/50 "
                    "px-3 py-2 text-sm text-slate-800 focus:border-[#28a745] "
                    "focus:bg-white focus:outline-none focus:ring-2 "
                    "focus:ring-[#28a745]/20"
                )
        for field_name, errors in context["form"].errors.items():
            if field_name in context["form"].fields and errors:
                context["form"].fields[field_name].widget.attrs.update(
                    {
                        "aria-invalid": "true",
                        "aria-describedby": f"id_{field_name}-errors",
                    }
                )
        return context


@login_required(login_url="users_app:user-login")
def email_notifications_settings(request, pk):
    """Update user email notificationd agreement."""

    if request.method == 'POST':
        email = request.POST.get("email", None)
        agreement = request.POST.get("agreement", False)
        bool_agreement = True if agreement == "on" else False
        user_to_update = User.objects.get(id=pk)
        if user_to_update and email:
            user_to_update.email = email
            user_to_update.email_notifications = bool_agreement
            user_to_update.save()
    return HttpResponseRedirect(reverse("home_app:index"))


@login_required(login_url="users_app:user-login")
@user_passes_test(check_staff)
@require_POST
def delete_employee(request, pk):
    """Permanently deletes an employee. Request.author and Sickleave.employee
    are on_delete=CASCADE, so this also removes all of their leave requests
    and sick leaves, as disclosed in the confirmation dialog."""
    employee = get_object_or_404(User, pk=pk)
    requests_count = Request.objects.filter(author=employee).count()
    sickleaves_count = Sickleave.objects.filter(employee=employee).count()
    logger.warning(
        "User %s (id=%s) deleted by %s, cascading %s requests and %s "
        "sick leaves",
        employee.username, employee.pk, request.user.username,
        requests_count, sickleaves_count,
    )
    with transaction.atomic():
        employee.delete()
    return HttpResponseRedirect(reverse("users_app:admin-all-employees"))


@login_required(login_url="users_app:user-login")
@user_passes_test(check_staff)
def add_annual_leave(request):
    """Tool to add at the beginning of the year all employees annual leave
    entitlement to their current leave entitlement."""
    for employee in User.objects.filter(is_active=True):
        employee.current_leave += employee.annual_leave
        employee.save()
    return HttpResponseRedirect(reverse("users_app:admin-all-employees"))


@require_POST
def subscription_check(request):
    try:
        post_data = json.loads(request.body.decode("utf-8"))
        subscription_endpoint = post_data["subscription"]["endpoint"]
    except (ValueError, KeyError):
        return HttpResponse(status=400)

    if PushInformation.objects.filter(
        subscription__endpoint=subscription_endpoint, user=request.user
    ).exists():
        return HttpResponse(status=200)
    return HttpResponse(status=240)
