import django_filters
import logging
import operator
from functools import reduce
from datetime import date, timedelta
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.http import HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.forms.widgets import Select, TextInput

from applications.users.mixins import (
    TopManagerPermisoMixin,
    check_occupation_user,
)
from .models import Sickleave, EZLAReportDownload
from .forms import SickleaveForm
from .utils import (
    SickleaveNotification,
    SickAndAnnulalLeaveOverlappedAlertMixin,
    ModalSickleaveNotification
)
from .ezla import get_compiled_ezla_data


logger = logging.getLogger("django")


class FilteredListView(ListView):
    filterset_class = None

    def get_queryset(self):
        queryset = Sickleave.objects.all().order_by("-issue_date")
        self.filterset = self.filterset_class(
            self.request.GET, queryset=queryset
        )
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        return context


class SickleavesFilter(django_filters.FilterSet):
    def get_years_choices():
        current_year = date.today().year
        years_choices = tuple(
            (year, year) for year in list(range(2022, current_year + 1))
        )
        return years_choices

    YEARS_CHOICES = get_years_choices()

    dropdown_field = django_filters.ChoiceFilter(
        method="filter_year",
        choices=YEARS_CHOICES,
        label="Wybierz rok",
        empty_label="Rok",
        widget=Select(attrs={"class": "form-control"}),
    )
    other_fields = django_filters.CharFilter(
        method="filter_other_fields",
        label="Wyszukaj",
        widget=TextInput(
            attrs={"class": "form-control", "placeholder": "Wyszukaj..."}
        ),
    )

    class Meta:
        model = Sickleave
        fields = ["other_fields", "dropdown_field"]

    @staticmethod
    def filter_other_fields(qs, name, value):
        query_words = value.split()
        return qs.filter(
            reduce(
                operator.and_,
                (
                    Q(employee__first_name__icontains=word)
                    | Q(employee__last_name__icontains=word)
                    for word in query_words
                ),
            )
            | Q(start_date__icontains=value)
            | Q(end_date__icontains=value)
            | Q(issue_date__icontains=value)
            | Q(additional_info__icontains=value)
        )

    @staticmethod
    def filter_year(qs, name, value):
        return qs.filter(Q(start_date__year=value) | Q(end_date__year=value))


class SickleavesListView(FilteredListView):
    """Sick leaves listing page."""

    filterset_class = SickleavesFilter

    context_object_name = "sickleaves"
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_download_report = EZLAReportDownload.objects.last()
        if last_download_report:
            context[
                "last_report_date"
            ] = last_download_report.last_download_date
        context["ezla"] = getattr(settings, "EZLA_URL", None)
        return context


class SickleaveCreateView(
    TopManagerPermisoMixin, SickAndAnnulalLeaveOverlappedAlertMixin, CreateView
):
    """Sick leave registration form."""

    template_name = "sickleaves/add_sickleave.html"
    model = Sickleave
    form_class = SickleaveForm
    success_url = reverse_lazy("sickleaves_app:sickleaves")
    login_url = reverse_lazy("users_app:user-login")

    def form_valid(self, form):
        try:
            notification = SickleaveNotification(form)
            notification.send_notification()
        except Exception:
            logger.error(
                "Email notification about sickleave was not sent",
                exc_info=True,
            )
        return super(SickleaveCreateView, self).form_valid(form)


class SickleaveUpdateView(
    TopManagerPermisoMixin, SickAndAnnulalLeaveOverlappedAlertMixin, UpdateView
):
    """Sickleave update form."""

    model = Sickleave
    template_name = "sickleaves/update_sickleave.html"
    fields = "__all__"
    success_url = reverse_lazy("sickleaves_app:sickleaves")
    login_url = reverse_lazy("users_app:user-login")


@login_required(login_url="users_app:user-login")
@user_passes_test(check_occupation_user)
def delete_sickleave(request, pk):
    """Deletes sick leave."""
    Sickleave.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))


@login_required(login_url="users_app:user-login")
@user_passes_test(check_occupation_user)
def notify_about_sickleave(request, pk):
    """Send email notification about sick leave."""

    sickleave = Sickleave.objects.get(id=pk)
    if request.method == 'POST':
        head = request.POST.get("head")
        instructor = request.POST.get("instructor")
        manager = request.POST.get("manager")
        try:
            notification = ModalSickleaveNotification(
                head, instructor, manager, sickleave
                )
            notification.send_notification()
        except Exception:
            logger.error(
                "Email notification about sickleave was not sent",
                exc_info=True,
            )
    return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))


@login_required(login_url="users_app:user-login")
@user_passes_test(check_occupation_user)
def get_ezla(request):
    """Get and save sick leaves from polish ZUS service."""
    today = date.today()

    last_download_report = EZLAReportDownload.objects.last()
    if last_download_report:
        last_download_date = last_download_report.last_download_date
        date_since = last_download_date + timedelta(days=1)
    else:
        date_since = today - timedelta(days=1)
        last_download_report = EZLAReportDownload.objects.create(
            last_download_date=date_since
        )

    if date_since < (today - timedelta(days=28)):
        date_since = today - timedelta(days=28)

    data = get_compiled_ezla_data(date_since)
    users = get_user_model()

    if isinstance(data, list) and not data:
        messages.success(request, "Brak nowych zwolnień do pobrania.")
        last_download_report.last_download_date = today
        last_download_report.save()
        return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))

    if isinstance(data, list) and len(data):
        for sickleave in data:
            sick_empl_first_name = sickleave.get("first_name")
            sick_empl_last_name = sickleave.get("last_name")
            empl = users.objects.filter(
                first_name=sick_empl_first_name, last_name=sick_empl_last_name
            )
            sick_employee = empl.first()

            if sick_employee is None:
                messages.error(
                    request,
                    ("Nie udało się zapisać zwolnienia dla: "
                        f"{sick_empl_first_name} {sick_empl_last_name}")
                )
            else:
                try:
                    doc_number = sickleave.get("doc_number")
                    issue_date = sickleave.get("issue_date")
                    sickleave_in_db = Sickleave.objects.filter(
                        doc_number=doc_number, issue_date=issue_date
                    )
                    if sickleave_in_db:
                        sickleave_in_db.update(
                            leave_type=sickleave.get("leave_type"),
                            start_date=sickleave.get("start_date"),
                            end_date=sickleave.get("end_date"),
                            additional_info=sickleave.get("additional_info"),
                        )
                        messages.warning(
                            request,
                            ("Zaktualizowano zwolnienie dla: "
                                f"{sick_empl_first_name} {sick_empl_last_name}")  # noqa: E501
                        )
                    else:
                        s = Sickleave(
                            employee=sick_employee,
                            leave_type=sickleave.get("leave_type"),
                            issue_date=issue_date,
                            doc_number=doc_number,
                            start_date=sickleave.get("start_date"),
                            end_date=sickleave.get("end_date"),
                            additional_info=sickleave.get("additional_info"),
                        )
                        s.save()
                        messages.success(
                            request,
                            (f"Pobrano zwolnienie dla: {sick_empl_first_name} "
                                f"{sick_empl_last_name}"),
                        )

                except Exception as e:
                    logger.error(
                        f"Błąd podczas zapisywania zwolnienia do bazy: {e}"
                    )
                    messages.error(
                        request,
                        ("Błąd podczas zapisywania zwolnienia do bazy u: "
                            f"{sick_empl_first_name} {sick_empl_last_name}")
                    )
        last_download_report.last_download_date = today
        last_download_report.save()

    else:
        messages.error(request, data)

    return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))
