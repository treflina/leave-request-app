from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, CreateView, FormView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from applications.users.models import User
from applications.users.mixins import TopManagerPermisoMixin
from .models import UploadFile, CATEGORY_CHOICES
from .forms import ReportForm
from pdf_creator import create_pdf_report


class HomePage(LoginRequiredMixin, TemplateView):

    template_name = "home/index.html"
    model = User
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.working_hours < 1:
            context["part"] = True
        if self.request.user.current_leave == 1:
            context["onedayleft"] = True
        if self.request.user.role == "S":
            context["show_director"] = True
        if self.request.user.role == "T" or self.request.user.role == "K":
            context["show_manager"] = True

        return context


class ReportView(TopManagerPermisoMixin, FormView):
    """Creates pdf report about leave requests and sickleaves for a chosen time period."""

    form_class = ReportForm
    template_name = "home/report.html"
    success_url = "."
    login_url = reverse_lazy("users_app:user-login")

    def form_valid(self, form):
        person = form.cleaned_data["person"]
        leave_type = form.cleaned_data["leave_type"]
        start = form.cleaned_data["start_date"]
        end = form.cleaned_data["end_date"]
        attachment = form.cleaned_data["attachment"]

        return create_pdf_report(
            person=person,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            attachment=attachment,
        )


class UploadFileView(LoginRequiredMixin, CreateView):

    model = UploadFile
    template_name = "home/files.html"
    fields = ["file", "description", "category", "priority"]
    success_url = "."
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        titles = [category[1] for category in CATEGORY_CHOICES]
        data = []
        cat_dict = {}
        for category in CATEGORY_CHOICES:
            cat_files = UploadFile.objects.filter(category=category[0]).order_by(
                "priority"
            )
            cat_dict[category[1]] = cat_files
            data.append(cat_dict[category[1]])
        context["categories"] = zip(titles, data)

        if "informatyk" in self.request.user.position:
            context["informatyk"] = True
        return context


@login_required(login_url=reverse_lazy("users_app:user-login"))
def delete_file(request, pk):
    """Deletes the file."""
    file_to_delete = UploadFile.objects.get(id=pk)
    file_to_delete.delete()
    return HttpResponseRedirect(reverse("home_app:documents"))
