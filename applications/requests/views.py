import logging
import operator
import django_filters

from functools import reduce
from simple_history.utils import update_change_reason
from webpush.utils import send_to_subscription
from webpush import send_user_notification

from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, ListView, UpdateView
from django.forms.widgets import Select, TextInput, DateInput

from applications.users.models import User
from applications.users.mixins import TopManagerPermisoMixin

from .models import Request
from .forms import RequestForm, UpdateRequestForm
from .utils import RequestEmailNotification
from paginator import PaginationMixin


logger = logging.getLogger("django")


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
        leave_type = form.cleaned_data["leave_type"]

        days = form.cleaned_data["days"]
        if leave_type == "WS" or leave_type == "WN" or leave_type == "DW":
            days = 0

        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        work_date = form.cleaned_data["work_date"]

        duvet_day = bool(form.cleaned_data.get("duvet_day"))
        if leave_type != "W":
            duvet_day = None

        send_to_person = form.cleaned_data["send_to_person"]

        if (leave_type == "WS" or leave_type == "WN") and Request.objects.filter(
            Q(author=user)
            & Q(work_date=work_date)
            & ~Q(status="odrzucony")
            & ~Q(status="anulowany")
        ).exists():
            messages.error(
                self.request,
                """Błąd. Wniosek o odebranie dnia wolnego za wskazaną pracującą
                sobotę/niedzielę został już złożony.""",
            )
            return self.form_invalid(form)

        Request(
            author=user,
            leave_type=leave_type,
            work_date=work_date,
            start_date=start_date,
            end_date=end_date,
            days=days,
            duvet_day=duvet_day,
            substitute=form.cleaned_data["substitute"],
            send_to_person=send_to_person,
        ).save()

        user.current_leave -= days
        user.save(update_fields=["current_leave"])
        messages.success(self.request, "Wniosek został pomyślnie złożony.")

        try:
            notification = RequestEmailNotification(
                user,
                leave_type,
                start_date,
                end_date,
                work_date,
                duvet_day,
                send_to_person,
            )
            notification.send_notification()
        except Exception:
            logger.error("Email request notification not sent", exc_info=True)

        try:
            payload = {
                "head": "Nowy wniosek do zaopiniowania",
                "body": f"""{user} prosi o akceptację wniosku ({leave_type}) \
    od {start_date} do {end_date}.""",
                "url": reverse("requests_app:allrequests"),
            }
            recipient = send_to_person
            send_user_notification(user=recipient, payload=payload, ttl=1000)

        except Exception:
            logger.error("Notification was not sent", exc_info=True)

        return super(RequestFormView, self).form_valid(form)


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
            (Q(role="K") | Q(role="S") | Q(role="T")) & Q(is_active=True)
        ).order_by("last_name")

        if self.object.author.working_hours < 1:
            context["part"] = True

        history_changereason = (
            Request.history.filter(id=self.object.id).first().history_change_reason
        )
        if history_changereason in ["None", "", None]:
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


class UserRequestsListView(LoginRequiredMixin, PaginationMixin, ListView):
    """Authenticated user leave requests listing view."""

    template_name = "requests/user_requests.html"
    model = Request
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(UserRequestsListView, self).get_context_data(**kwargs)
        user = self.request.user
        user_requests_holiday = Request.objects.user_requests_holiday(user)
        user_requests_other = Request.objects.user_requests_other(user)

        context["user_requests_holiday"] = self.paginate(user_requests_holiday, "page")
        context["user_requests_other"] = self.paginate(user_requests_other, "page2")

        return context


class RequestsFilteredListView(ListView):
    filterset_class = None

    def get_queryset(self):
        queryset = Request.objects.all().order_by("-start_date")
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        return context


class RequestsFilter(django_filters.FilterSet):
    """Filter for listing leave requests views."""

    LEAVE_TYPE_CHOICES = [("W", "W"), ("WS", "WS"), ("WN", "WN"), ("DW", "DW")]

    dropdown_field = django_filters.ChoiceFilter(
        field_name="leave_type",
        lookup_expr="exact",
        choices=LEAVE_TYPE_CHOICES,
        label="Wybierz rodzaj wolnego",
        empty_label="Rodzaj",
        widget=Select(attrs={"class": "form-control"}),
    )
    start_date = django_filters.DateFilter(
        field_name="start_date",
        lookup_expr="gte",
        label="Od:",
        widget=DateInput(
            format="%d.%m.%y",
            attrs={
                "class": "form-control",
                "type": "date",
            },
        ),
    )
    end_date = django_filters.DateFilter(
        field_name="end_date",
        lookup_expr="lte",
        label="Do:",
        widget=DateInput(
            format="%d.%m.%y",
            attrs={
                "class": "form-control",
                "type": "date",
            },
        ),
    )

    other_fields = django_filters.CharFilter(
        method="filter_other_fields",
        label="Wyszukaj",
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Wyszukaj..."}),
    )

    class Meta:
        model = Request
        fields = [
            "dropdown_field",
            "start_date",
            "end_date",
            "other_fields",
        ]

    @staticmethod
    def filter_other_fields(qs, name, value):
        query_words = value.split()
        return qs.filter(
            reduce(
                operator.and_,
                (
                    Q(author__first_name__icontains=word)
                    | Q(author__last_name__icontains=word)
                    for word in query_words
                ),
            )
            | Q(start_date__icontains=value)
            | Q(end_date__icontains=value)
            | Q(work_date__icontains=value)
            | Q(status__icontains=value)
        )

    @staticmethod
    def filter_year(qs, name, value):
        return qs.filter(Q(start_date__year=value) | Q(end_date__year=value))


class RequestsListView(TopManagerPermisoMixin, ListView):
    """Leave requests listing view for managers where they can accept or reject
    reuests they have received.
    Topmanagers can view requests sent from all employees."""

    context_object_name = "requests_holiday"
    template_name = "requests/allrequests.html"
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.role == "T" or user.role == "S" or user.is_staff:
            queryset = Request.objects.all().order_by("-start_date")
        elif user.role == "K":
            queryset = Request.objects.filter(author__manager=user)
        else:
            queryset = None
        filter = RequestsFilter(self.request.GET, queryset)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        filter = RequestsFilter(self.request.GET, queryset)
        context["filterset"] = filter
        context["requests_received"] = Request.objects.requests_to_accept(
            self.request.user
        )
        return context


class HRAllRequestsListView(TopManagerPermisoMixin, ListView):
    """All employees requests listing page for HR department."""

    context_object_name = "requests_holiday"
    template_name = "requests/hrallrequests.html"
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 20

    def get_queryset(self):
        queryset = Request.objects.all().order_by("-start_date")
        filter = RequestsFilter(self.request.GET, queryset)
        return filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        filter = RequestsFilter(self.request.GET, queryset)
        context["filterset"] = filter
        return context


def accept_request(request, pk):
    """Accept the employee request."""
    user = request.user
    request_to_accept = Request.objects.get(id=pk)
    request_to_accept.status = "zaakceptowany"
    request_to_accept.signed_by = user.first_name + " " + user.last_name
    request_to_accept.save(update_fields=["status", "signed_by"])
    try:
        payload = {
            "head": "Wniosek został zaakceptowany",
            "body": f"""Wniosek ({request_to_accept.leave_type}) {request_to_accept.start_date} \
do {request_to_accept.end_date} został zaakceptowany.""",
        }
        employee = request_to_accept.author
        send_user_notification(user=employee, payload=payload, ttl=1000)

    except Exception:
        logger.error("Notification was not sent", exc_info=True)
    return HttpResponseRedirect(reverse("requests_app:allrequests"))


def reject_request(request, pk):
    """Reject the employee request."""
    user = request.user
    request_to_reject = Request.objects.get(id=pk)
    if request_to_reject.leave_type == "W":
        employee_to_update = User.objects.get(id=request_to_reject.author.id)
        employee_to_update.current_leave += request_to_reject.days
        employee_to_update.save(update_fields=["current_leave"])
    request_to_reject.status = "odrzucony"
    request_to_reject.signed_by = user.first_name + " " + user.last_name
    request_to_reject.save(update_fields=["status", "signed_by"])
    try:
        payload = {
            "head": "Wniosek został odrzucony",
            "body": f"""Wniosek ({request_to_reject.leave_type}) {request_to_reject.start_date} \
do {request_to_reject.end_date} został odrzucony.""",
        }
        employee = request_to_reject.author
        send_user_notification(user=employee, payload=payload, ttl=1000)

    except Exception:
        logger.error("Notification was not sent", exc_info=True)

    return HttpResponseRedirect(reverse("requests_app:allrequests"))


def delete_request(request, pk):
    """Withdraw the request."""
    user = request.user
    request_to_delete = Request.objects.get(id=pk)
    if request_to_delete.leave_type == "W":
        user.current_leave += request_to_delete.days
        user.save(update_fields=["current_leave"])
    request_to_delete.delete()
    return HttpResponseRedirect(reverse("requests_app:user_requests"))
