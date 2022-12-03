from datetime import datetime
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from applications.users.mixins import TopManagerPermisoMixin
from applications.requests.models import Request
from .models import Sickleave
from .forms import SickleaveForm
from .utils import SickleaveNotification, SickAndAnnulalLeaveOverlappedAlertMixin

import logging

logger = logging.getLogger("django")


class SickleavesListView(TopManagerPermisoMixin, ListView):
    """Sick leaves listing page."""

    context_object_name = "sickleaves"
    template_name = "sickleaves/sickleaves.html"
    login_url = reverse_lazy("users_app:user-login")

    def get_queryset(self):
        return Sickleave.objects.all().order_by("-issue_date")


class SickleaveCreateView(TopManagerPermisoMixin, SickAndAnnulalLeaveOverlappedAlertMixin, CreateView):
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


class SickleaveUpdateView(TopManagerPermisoMixin, SickAndAnnulalLeaveOverlappedAlertMixin, UpdateView):
    """Sickleave update form."""

    model = Sickleave
    template_name = "sickleaves/update_sickleave.html"
    fields = "__all__"
    success_url = reverse_lazy("sickleaves_app:sickleaves")
    login_url = reverse_lazy("users_app:user-login")


@login_required(login_url="users_app:user-login")
def delete_sickleave(request, pk):
    """Deletes sick leave."""
    sickleave_to_delete = Sickleave.objects.get(id=pk).delete()
    return HttpResponseRedirect(reverse("sickleaves_app:sickleaves"))
