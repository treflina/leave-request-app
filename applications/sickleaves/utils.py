from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models.query_utils import Q

from wnioski.settings import get_secret
from applications.requests.models import Request

User = get_user_model()


class SickAndAnnulalLeaveOverlappedAlertMixin:
    """Mixin that displays a warning message when an employee has submitted
    a leave request for the same day as registered sick leave."""

    def form_valid(self, form):
        start = form.cleaned_data.get("start_date")
        end = form.cleaned_data.get("end_date")
        leave_type = form.cleaned_data.get("leave_type")
        employee = form.cleaned_data.get("employee")
        employee_leave_requests = Request.objects.filter(
            Q(author=employee)
            & ~Q(status="odrzucony")
            & (
                Q(start_date__range=[start, end])
                | Q(end_date__range=[start, end])
            )
        )
        if employee_leave_requests.exists() and leave_type != "O":
            messages.warning(
                self.request,
                (
                    f"{employee.first_name} {employee.last_name} złożył/a "
                    "wniosek o urlop wypoczynkowy w podanym okresie "
                    f"zwolnienia lekarskiego ({(start.strftime('%d.%m.%y'))}-"
                    f"{end.strftime('%d.%m.%y')}). "
                    "Pamiętaj o anulowaniu tego wniosku i zaktualizowaniu "
                    "przysługującego pracownikowi wymiaru urlopu."
                ),
            )
        elif employee_leave_requests.exists() and leave_type == "O":
            messages.warning(
                self.request,
                (
                    f"Zwolnienie zostało poprawnie zapisane, ale "
                    f"{employee.first_name} {employee.last_name} "
                    "złożył/a wniosek o urlop wypoczynkowy w podanym "
                    f"okresie ({(start.strftime('%d.%m.%y'))}-"
                    f"{end.strftime('%d.%m.%y')}) "
                    "sprawowania opieki nad chorym członkiem rodziny."
                )
            )

        return super().form_valid(form)


class SickleaveNotificationMixin:
    """Send email notification about sick leave."""

    def send_notification(self):
        if self.leave_type == "O":
            text = "na opiece nad chorym członkiem rodziny"
            text_subj = "opieka"
        elif self.leave_type == "K":
            text = "na kwarantannie"
            text_subj = "kwarantanna"
            self.text_info = "Podane daty mogą ulec zmianie."
        elif self.leave_type == "I":
            text = "na izolacji"
            text_subj = "izolacja"
        else:
            text = f"na zwolnieniu lekarskim ({self.leave_type})"
            text_subj = "chorobowe"

        subject = (
            f"{text_subj} {self.employee.first_name} "
            f"{self.employee.last_name} "
            f"({self.start_date} - {self.end_date})"
            )
        message = (
            f"Dzień dobry,\r\n{self.employee.first_name} "
            f"{self.employee.last_name} przebywa {text} "
            f"w dniach {self.start_date} do {self.end_date}. "
            f"{self.text_info}\r\n \r\nWiadomość wygenerowana automatycznie."
        )
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")

        send_to_people = []
        if self.head:
            person = User.objects.filter(Q(role="S")).first()
            if person:
                send_to_people.append(person.work_email)
        if self.manager:
            person = User.objects.filter(
                Q(id=self.employee.manager.id)
            ).first()
            if person:
                send_to_people.append(person.work_email)
        if self.instructor:
            person = User.objects.filter(
                Q(role="T") & Q(position__icontains="instruktor")
            ).first()
            if person:
                send_to_people.append(person.work_email)

        send_to_people_list = [p for p in set(send_to_people)] + [
            EMAIL_HOST_USER
        ]

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            send_to_people_list,
            fail_silently=False,
        )


class SickleaveNotification(SickleaveNotificationMixin):
    """Sending email notification about sick leave
    using it's creation form."""

    def __init__(self, form):
        self.form = form
        self.employee = self.form.cleaned_data["employee"]
        self.start_date = self.form.cleaned_data["start_date"].strftime(
            "%d.%m.%y"
        )
        self.end_date = self.form.cleaned_data["end_date"].strftime("%d.%m.%y")
        self.leave_type = self.form.cleaned_data["leave_type"]
        self.head = self.form.cleaned_data["head"]
        self.manager = self.form.cleaned_data["manager"]
        self.instructor = self.form.cleaned_data["instructor"]
        self.text_info = ""


class ModalSickleaveNotification(SickleaveNotificationMixin):
    """Sending email notification about sick leave that's been already saved
    in the database."""

    def __init__(self, head, instructor, manager, sickleave):
        self.sickleave = sickleave
        self.employee = self.sickleave.employee
        self.start_date = self.sickleave.start_date.strftime(
            "%d.%m.%y"
        )
        self.end_date = self.sickleave.end_date.strftime(
            "%d.%m.%y"
        )
        self.leave_type = self.sickleave.leave_type
        self.head = head
        self.manager = manager
        self.instructor = instructor
        self.text_info = ""
