from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.query_utils import Q
from wnioski.settings import get_secret

User = get_user_model()


class SickleaveNotification:
    def __init__(self, form):
        self.form = form
        self.employee = self.form.cleaned_data["employee"]
        self.start_date = self.form.cleaned_data["start_date"].strftime("%d.%m.%y")
        self.end_date = self.form.cleaned_data["end_date"].strftime("%d.%m.%y")
        self.type = self.form.cleaned_data["type"]
        self.head = self.form.cleaned_data["head"]
        self.manager = self.form.cleaned_data["manager"]
        self.instructor = self.form.cleaned_data["instructor"]
        self.text_info = ""

    def send_notification(self):
        if self.type == "O":
            text = "na opiece nad chorym członkiem rodziny"
            text_subj = f"opieka"
        elif self.type == "K":
            text = "na kwarantannie"
            text_subj = f"kwarantanna"
            self.text_info = f"Podane daty mogą ulec zmianie."
        elif self.type == "I":
            text = "na izolacji"
            text_subj = f"izolacja"
        else:
            text = f"na zwolnieniu lekarskim ({self.type})"
            text_subj = f"chorobowe"

        subject = f"{text_subj} {self.employee.first_name} {self.employee.last_name} ({self.start_date} - {self.end_date})"
        message = f"Dzień dobry,\r\n{self.employee.first_name} {self.employee.last_name} przebywa {text} w dniach {self.start_date} do {self.end_date}. {self.text_info}\r\n \r\nWiadomość wygenerowana automatycznie."
        EMAIL_HOST_USER = get_secret("EMAIL_HOST_USER")
        if self.employee.manager:
            send_to_people = []
            if self.head:
                person = User.objects.filter(Q(role="S")).first()
                send_to_people.append(person.work_email)
            if self.manager:
                person = User.objects.filter(Q(id=self.employee.manager.id)).first()
                send_to_people.append(person.work_email)
            if self.instructor:
                person = User.objects.filter(
                    Q(role="T") & Q(position__icontains="instruktor")
                ).first()
                send_to_people.append(person.work_email)

            send_to_people_list = [p for p in set(send_to_people)] + [EMAIL_HOST_USER]
            print(send_to_people_list)

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                send_to_people_list,
                fail_silently=False,
            )
