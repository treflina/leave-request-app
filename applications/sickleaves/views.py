import logging
import operator
from functools import reduce
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


logger = logging.getLogger("django")


class FilteredListView(ListView):
    filterset_class = None

    def get_queryset(self):
        queryset = Sickleave.objects.all().order_by("-issue_date")
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
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
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Wyszukaj..."})
        )

    class Meta:
        model = Sickleave
        fields = [
            "other_fields",
            "dropdown_field"
        ]

    @staticmethod
    def filter_other_fields(qs, name, value):
        query_words = value.split()
        return qs.filter(
            reduce(
                operator.and_,
                (
                    Q(employee__first_name__icontains=word) |
                    Q(employee__last_name__icontains=word)
                    for word in query_words
                ),
            ) |
            Q(start_date__icontains=value) |
            Q(end_date__icontains=value) |
            Q(issue_date__icontains=value) |
            Q(additional_info__icontains=value)
        )

    @staticmethod
    def filter_year(qs, name, value):
        return qs.filter(
            Q(start_date__year=value) |
            Q(end_date__year=value)
        )


class SickleavesListView(FilteredListView):
    """Sick leaves listing page."""

    filterset_class = SickleavesFilter

    context_object_name = "sickleaves"
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy("users_app:user-login")
    paginate_by = 20


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
