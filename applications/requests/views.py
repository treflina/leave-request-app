from simple_history.utils import update_change_reason

from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, ListView, UpdateView
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger

from applications.users.models import User
from applications.users.mixins import TopManagerPermisoMixin

from .models import Request
from .forms import RequestForm, UpdateRequestForm
from .utils import RequestEmailNotification

import logging

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
            Q(author=user) & Q(work_date=work_date) & ~Q(status="odrzucony")
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


class UserRequestsListView(LoginRequiredMixin, ListView):
    """Authenticated user requests listing page."""

    template_name = "requests/user_requests.html"
    model = Request
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super(UserRequestsListView, self).get_context_data(**kwargs)
        user = self.request.user
        user_requests_holiday = Request.objects.user_requests_holiday(user)
        paginator = Paginator(user_requests_holiday, self.paginate_by)

        page = self.request.GET.get('page')

        try:
            user_requests_holiday = paginator.page(page)
        except PageNotAnInteger:
            user_requests_holiday = paginator.page(1)
        except EmptyPage:
            user_requests_holiday = paginator.page(paginator.num_pages)

        context['user_requests_holiday'] = user_requests_holiday

        user_requests_other = Request.objects.user_requests_other(user)
        paginator = Paginator(user_requests_other, self.paginate_by)

        page = self.request.GET.get('page2')

        try:
            user_requests_other = paginator.page(page)
        except PageNotAnInteger:
            user_requests_other = paginator.page(1)
        except EmptyPage:
            user_requests_other = paginator.page(paginator.num_pages)

        context['user_requests_other'] = user_requests_other

        return context


class RequestsListView(TopManagerPermisoMixin, ListView):
    """List view that contains 30 last requests from subordinates
    since the beginning of the year and up to the following 3 weeks."""

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
    """All employees requests listing page for HR department. It contains all requests
    except those sent by current user themselves."""

    model = Request
    template_name = "requests/hrallrequests.html"
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):

        context = super(HRAllRequestsListView, self).get_context_data(**kwargs)
        context["requests_holiday"] = Request.objects.hrallrequests_holiday()
        context["requests_other"] = Request.objects.hrallrequests_other()
        return context


class AllHolidayRequestsListView(TopManagerPermisoMixin, ListView):
    """All holiday employees requests listing page. It contains all requests except
    those sent by current user themselves."""

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
    """All other employees requests listing page. It contains all requests except
    those sent by current user themselves."""

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
    if request_to_reject.leave_type == "W":
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
    if request_to_delete.leave_type == "W":
        user.current_leave += request_to_delete.days
        user.save(update_fields=["current_leave"])
    request_to_delete.delete()
    return HttpResponseRedirect(reverse("requests_app:user_requests"))
