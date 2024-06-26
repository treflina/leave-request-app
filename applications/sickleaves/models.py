from django.db import models
from django.conf import settings

from .managers import SickleavesSearchManager


class Sickleave(models.Model):
    """Sickleave model."""

    LEAVE_TYPE_CHOICES = (
        ("C", "Chorobowe"),
        ("O", "Opieka"),
        ("K", "Kwarantanna"),
        ("I", "Izolacja"),
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="osoba",
        related_name="sickemployee",
        default="",
    )
    leave_type = models.CharField(
        "Rodzaj", max_length=10, choices=LEAVE_TYPE_CHOICES, default="C"
    )
    issue_date = models.DateField("Data wystawienia", null=True, blank=True)
    doc_number = models.CharField(
        "Nr dokumentu", max_length=20, null=True, blank=True
    )
    start_date = models.DateField("Od", null=True)
    end_date = models.DateField("Do", null=True)
    additional_info = models.CharField(
        "Dodatkowe informacje", max_length=50, blank=True
    )

    objects = SickleavesSearchManager()

    class Meta:
        verbose_name = "Zwolnienie lekarskie"
        verbose_name_plural = "Zwolnienia lekarskie"
        ordering = ["issue_date"]

    def __str__(self):
        return f"""{self.employee.last_name} {self.employee.first_name}
            od {str(self.start_date)} do {str(self.end_date)}"""


class EZLAReportDownload(models.Model):
    """Model for reports downloaded from polish ZUS."""

    last_download_date = models.DateField(verbose_name="ostatnie pobranie")

    class Meta:
        verbose_name = "Ostatnie pobranie raportu z ZUS"
        verbose_name_plural = "Ostatnie pobranie raportu z ZUS"

    def __str__(self):
        return f"""Pobrano: {self.last_download_date}"""


class EZLAReportGeneration(models.Model):
    """Model for reports downloaded from polish ZUS."""

    last_report_date = models.DateField(
        verbose_name="ostatni wygenerowany raport",
        null=True,
        blank=True
        )

    class Meta:
        verbose_name = "Ostatni wygenerowany raport z ZUS"
        verbose_name_plural = "Ostatni wygenerowany raport z ZUS"

    def __str__(self):
        return f"""Wygenerowanie: {self.last_report_date}"""
