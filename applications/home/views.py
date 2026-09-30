from datetime import date, timedelta

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.views.generic import TemplateView, CreateView, FormView
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from applications.requests.models import Request
from applications.users.models import User
from applications.users.mixins import StaffAndDirectorPermissionMixin
from .models import UploadFile, CATEGORY_CHOICES
from .forms import ReportForm
from pdf_creator import create_pdf_report, create_text_report


def can_manage_documents(user):
    return user.is_authenticated and (
        user.is_staff
        or user.role in {"T", "S"}
        or "informatyk" in user.position.casefold()
    )


class HomePage(LoginRequiredMixin, TemplateView):

    template_name = "home/index.html"
    model = User
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.request.user
        current_year = date.today().year

        context["part"] = user.working_hours < 1
        context["onedayleft"] = user.current_leave == 1
        context["show_director"] = user.role == "S"
        context["show_manager"] = user.role in ("T", "K")

        if user.role != "S":
            upcoming_leaves_all = Request.objects.filter(
                start_date__year=current_year
            ).filter(
                start_date__gte=date.today()
            ).exclude(status="odrzucony"
                      ).exclude(status="anulowany")

            if user.role in {"K", "T"} and user.user.all():
                upcoming_leaves_count = upcoming_leaves_all.count()
                upcoming_leaves = upcoming_leaves_all.filter(
                    Q(author=user) | Q(author__manager=user)
                )
                context["manager"] = True
                context["upcoming_leaves_count"] = upcoming_leaves_count
            else:
                upcoming_leaves = upcoming_leaves_all.filter(author=user)
            context["upcoming_leaves"] = (
                upcoming_leaves.select_related("author")
                .order_by("start_date")[:3]
            )
        else:
            context["upcoming_leaves"] = []
            context["upcoming_end_of_contracts"] = (
                User.objects.filter(
                    contract_end__gte=date.today()).filter(
                        contract_end__lte=date.today()+timedelta(
                            days=61)).order_by("contract_end")
            )
        context["current_year"] = current_year

        context["user_messages"] = user.message_set.all()

        context["main_page"] = True

        return context


class ReportView(StaffAndDirectorPermissionMixin, FormView):
    """Create a report about leave requests and sick leaves."""

    form_class = ReportForm
    template_name = "home/report.html"
    success_url = "."
    login_url = reverse_lazy("users_app:user-login")

    def form_valid(self, form):
        person = form.cleaned_data["person"]
        leave_type = form.cleaned_data["leave_type"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]
        attachment = form.cleaned_data["attachment"]
        report_format = form.cleaned_data["report_format"]

        if report_format == "certificate" and leave_type == "C":
            return create_text_report(
                person=person,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                attachment=attachment,
                report_format="certificate",
            )

        if report_format == "txt":
            return create_text_report(
                person=person,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                attachment=attachment,
            )

        return create_pdf_report(
            person=person,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            attachment=attachment,
        )


class UploadFileView(LoginRequiredMixin, CreateView):
    """Uploaded documents listing view. HR, topmanagers
    and users who are employed
    as informaticians can upload and delete files."""

    model = UploadFile
    template_name = "home/files.html"
    fields = ["file", "description", "category", "priority"]
    success_url = "."
    login_url = reverse_lazy("users_app:user-login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = []
        for cat, title in CATEGORY_CHOICES:
            cat_files = UploadFile.objects.filter(category=cat).order_by(
                "priority"
            )
            data.append((title, cat_files))
        context["categories"] = data
        context["can_manage_documents"] = can_manage_documents(
            self.request.user
        )
        return context


@login_required(login_url=reverse_lazy("users_app:user-login"))
@require_POST
def delete_file(request, pk):
    """Deletes the file."""
    if not can_manage_documents(request.user):
        raise PermissionDenied

    file_to_delete = get_object_or_404(UploadFile, pk=pk)
    file_to_delete.delete()
    return HttpResponseRedirect(reverse("home_app:documents"))


def robots_txt(request):
    content = """User-agent: *
Disallow: /
"""
    return HttpResponse(content, content_type="text/plain")
