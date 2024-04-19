from django.core.mail import send_mail
from django.conf import settings


class RequestEmailNotificationMixin:
    """Base mixin for sending emails about requests."""

    def __init__(self, leave_request):
        self.status = leave_request.status
        self.author = leave_request.author
        self.leave_type = leave_request.leave_type
        self.start_date = leave_request.start_date.strftime("%d.%m.%y")
        self.end_date = leave_request.end_date.strftime("%d.%m.%y")
        self.work_date = leave_request.work_date

    def prepare_email_content(self):
        if self.work_date:
            work_date = self.work_date.strftime("%d.%m.%y")

        if self.leave_type == "W" and self.start_date == self.end_date:
            text_msg = f"urlop wypoczynkowy w dniu {self.start_date}"
        elif self.leave_type == "W":
            text_msg = (
                f"urlop wypoczynkowy w okresie {self.start_date} - "
                f"{self.end_date}"
            )
        elif self.leave_type == "WS" or self.leave_type == "WN":
            text_msg = (
                f"dzień wolny ({self.leave_type}) {self.start_date} za pracę "
                f"{work_date}"
            )
        elif self.leave_type == "DW":
            text_msg = (
                f"dzień wolny {self.start_date} za święto przypadające w "
                "sobotę"
            )
        else:
            text_msg = (
                f"wolne ({self.leave_type}) w okresie "
                f"{self.start_date} - {self.end_date}"
            )
        return text_msg


class RequestEmailNotification(RequestEmailNotificationMixin):
    """Handles sending email to manager about a new leave request made by
    employee."""

    def __init__(self, leave_request, base_url):
        super().__init__(self, leave_request)
        self.base_url = base_url
        self.send_to_person = leave_request.send_to_person

    def send_notification(self):
        text_msg = self.prepare_email_content()

        subject = (
            f"{self.author} prosi o akceptację wniosku "
            f"({self.start_date}-{self.end_date})"
        )

        message = (
            f"{self.author} prosi o akceptację wniosku o "
            f"{text_msg}. \r\n \r\n"
            f"Zaopiniuj otrzymany wniosek na: {self.base_url} \r\n \r\n"
            f"Wiadomość wygenerowana automatycznie."
        )

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [self.send_to_person.work_email],
            fail_silently=False,
        )


class RequestChangedStatusEmailNotification(RequestEmailNotificationMixin):
    """Handles sending email to user about their request status change."""

    def send_notification(self):
        text_msg = self.prepare_email_content()

        subject = (
            f"Twój wniosek został {self.status}"
        )

        message = (
            f"Twój wniosek o {text_msg} został {self.status}. \r\n \r\n"
            f"Wiadomość wygenerowana automatycznie."
        )
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [self.author.email],
            fail_silently=False,
        )
