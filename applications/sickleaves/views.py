import django_filters
from datetime import date
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms.widgets import Select, TextInput

from applications.users.mixins import TopManagerPermisoMixin
from .models import Sickleave
from .forms import SickleaveForm
from .utils import SickleaveNotification, SickAndAnnulalLeaveOverlappedAlertMixin

import logging

logger = logging.getLogger("django")


class FilteredListView(ListView):
    filterset_class = None
    context_object_name = "sickleaves"
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy("users_app:user-login")

    def get_queryset(self):
        queryset = Sickleave.objects.all().order_by("-issue_date")
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset
        return context


class YearFilter(django_filters.FilterSet):
    def get_years_choices():
        current_year = date.today().year
        years_choices = tuple(
            (year, year) for year in list(range(2022, current_year + 1))
        )
        return years_choices

    YEARS_CHOICES = get_years_choices()

    issue_year = django_filters.ChoiceFilter(
        field_name="issue_date",
        lookup_expr="year",
        choices=YEARS_CHOICES,
        label="Wybierz rok",
        empty_label="Rok",
        widget=Select(attrs={"class": "form-control"}),
    )
    other_fields = django_filters.CharFilter(
        method="custom_filter",
        label="Wyszukaj",
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Wyszukaj..."})
        )

    class Meta:
        model = Sickleave
        fields = [
            "other_fields",
            "issue_year"
        ]

    @staticmethod
    def custom_filter(qs, name, value):
        return qs.filter(
            Q(employee__last_name__icontains=value) |
            Q(employee__first_name__icontains=value) |
            Q(start_date__icontains=value) |
            Q(end_date__icontains=value) |
            Q(issue_date__icontains=value) |
            Q(additional_info__icontains=value)
        )


class SickleavesListView(FilteredListView):
    """Sick leaves listing page."""

    filterset_class = YearFilter

    context_object_name = "sickleaves"
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 10


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
                "Email notification about sickleave was not sent", exc_info=True
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
def delete_sickleave(request, pk):
    """Deletes sick leave."""
    Sickleave.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))
