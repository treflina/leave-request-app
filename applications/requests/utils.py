from django.core.mail import send_mail
from django.conf import settings
from wnioski.settings import get_secret


class RequestEmailNotification:

    def __init__(self, author, type, start_date, end_date, work_date, duvet_day, send_to_person):
        self.author = author
        self.type = type
        self.start_date = start_date.strftime("%d.%m.%y")
        self.end_date = end_date.strftime("%d.%m.%y")
        self.work_date = work_date
        self.duvet_day = duvet_day
        self.send_to_person = send_to_person

    def send_notification(self):
        if self.work_date:
            work_date = self.work_date.strftime("%d.%m.%y")
        if self.type == "W" and self.start_date == self.end_date:
            text_msg = f"urlop wypoczynkowy w dniu {self.start_date}"
        elif self.type == "W":
            text_msg = f"urlop wypoczynkowy w okresie {self.start_date} - {self.end_date}"
        elif self.type == "WS" or self.type == "WN":
            text_msg = f"dzień wolny ({self.type}) {self.start_date} za pracę {work_date}"
        elif self.type == "DW":
            text_msg = f"dzień wolny {self.start_date} za święto przypadające w sobotę"
        else:
            text_msg = f"wolne ({self.type}) w okresie {self.start_date} - {self.end_date}"

        subject = f"{self.author} prosi o akceptację wniosku ({self.start_date}-{self.end_date})"
        message = f"{self.author} prosi o akceptację wniosku o {text_msg}.\r\n \r\nZaopiniuj otrzymany wniosek na: https://pracownik.mbp.opole.pl/ \r\n \r\nWiadomość wygenerowana automatycznie."
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [self.send_to_person.work_email],
            fail_silently=False,
        )