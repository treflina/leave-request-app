from email.policy import default
from django.db import models
from django.conf import settings

from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords
from applications.users.models import User
from applications.home.validators import FileValidator

from .managers import RequestManager


class Request(TimeStampedModel):
    """Request table model."""

    TYPE_CHOICES = (
        ("W", "Urlop wypoczynkowy (W)"),
        ("WS", "Wolne za pracującą sobotę (WS)"),
        ("WN", "Wolne za pracę w niedzielę/święto (WN)"),
        ("DW", "Wolne za święto przypadające w wolną sobotę (DW)"),
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="autor",
        on_delete=models.CASCADE,
        related_name="request_user",
        default="",
    )
    type = models.CharField("Rodzaj", max_length=30, choices=TYPE_CHOICES, default="")
    work_date = models.DateField("Data pracującej sob./nd/św.", null=True, blank=True)
    start_date = models.DateField("Od", null=True, blank=True)
    end_date = models.DateField("Do", null=True, blank=True)
    days = models.PositiveIntegerField("Ilość dni urlopu", null=True, blank=True)
    status = models.CharField(max_length=20, default="oczekujący")
    substitute = models.CharField("Zastępuje", max_length=40, blank=True)
    send_to_person = models.ForeignKey(
        User,
        verbose_name="wysłano do",
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_manager",
        default="",
    )
    signed_by = models.CharField("Zaopiniowany przez", max_length=50, blank=True)
    history = HistoricalRecords(history_change_reason_field=models.TextField(null=True))
    validate_file = FileValidator(
        max_size=1024 * 5000,
        content_types=(
            "application/pdf",
            "image/jpeg",
            "image/png",
        ),
    )
    attachment = models.FileField(
        "Załącznik",
        upload_to="attachments/",
        validators=[validate_file],
        null=True,
        blank=True,
    )

    objects = RequestManager()

    def __str__(self):
        if self.type == "W":
            return f"Wniosek ({self.type} od {self.start_date} do {self.end_date})"
        else:
            return f"Wniosek ({self.type}) {self.start_date}"

    class Meta:
        verbose_name = "Wnioski"
        verbose_name_plural = "Wnioski"
        ordering = ["-created"]


Request._meta.get_field("created").verbose_name = "złożony"
