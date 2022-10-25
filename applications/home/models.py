from django.db import models
from django.utils.translation import gettext as _
from .validators import FileValidator

CATEGORY_CHOICES = (
    ("regulaminy", "Regulaminy"),
    ("zarzadzenia", "Inne zarządzenia"),
    ("ppk", "Pracownicze Plany Kapitałowe"),
    ("pzu", "PZU Życie, PZU Opieka Medyczna"),
    ("zfss", "Zakładowy Fundusz Świadczeń Socjalnych"),
    ("inne", "Pozostałe"),
)
CONTENT_TYPES = (
    "text/plain",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
)


class UploadFile(models.Model):
    """Upload files model."""

    validate_file = FileValidator(max_size=1024 * 10000, content_types=CONTENT_TYPES)
    file = models.FileField("Plik", upload_to="documents/", validators=[validate_file])
    description = models.CharField("Opis", max_length=100, default="")
    category = models.CharField(
        "Kategoria", max_length=50, choices=CATEGORY_CHOICES, default="Pozostałe"
    )
    priority = models.IntegerField("Sortowanie (1-5)", default=2)
    show_as_new = models.BooleanField("Oznacz jako nowo dodany", default=False)

    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumenty"

    def __str__(self):
        return self.description
