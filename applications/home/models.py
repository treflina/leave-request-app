import magic

from django.db import models
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

CATEGORY_CHOICES = (
    ('regulaminy', 'Regulaminy'),
    ('zarzadzenia', 'Inne zarządzenia'),
    ('ppk', 'Pracownicze Plany Kapitałowe'),
    ('pzu', 'PZU Życie, PZU Opieka Medyczna'),
    ('zfss', 'Zakładowy Fundusz Świadczeń Socjalnych'),
    ('inne', 'Pozostałe'),
)
CONTENT_TYPES = (
    'text/plain',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
)

@deconstructible
class FileValidator(object):
    error_messages = {
        'max_size': "Upewnij się, że rozmiar pliku nie jest większy niż %(max_size)s.",
        'min_size': "Upewnij się, że rozmiar pliku nie jest mniejszy niż %(min_size)s.",
        'content_type': "Pliki typu %(content_type)s nie są obsługiwane.",
    }

    def __init__(self, max_size=None, min_size=None, content_types=()):
        self.max_size = max_size
        self.min_size = min_size
        self.content_types = content_types

    def __call__(self, data):
        if self.max_size is not None and data.size > self.max_size:
            params = {
                'max_size': filesizeformat(self.max_size),
                'size': filesizeformat(data.size),
            }
            raise ValidationError(self.error_messages['max_size'],
                                  'max_size', params)

        if self.min_size is not None and data.size < self.min_size:
            params = {
                'min_size': filesizeformat(self.min_size),
                'size': filesizeformat(data.size)
            }
            raise ValidationError(self.error_messages['min_size'],
                                  'min_size', params)

        if self.content_types:
            content_type = magic.from_buffer(data.read(), mime=True)
            data.seek(0)

            if content_type not in self.content_types:
                params = {'content_type': content_type}
                raise ValidationError(self.error_messages['content_type'],
                                      'content_type', params)


    def __eq__(self, other):
        return (
            isinstance(other, FileValidator) and
            self.max_size == other.max_size and
            self.min_size == other.min_size and
            self.content_types == other.content_types
        )


class UploadFile(models.Model):
    """Upload files model."""


    validate_file = FileValidator(max_size=1024 * 5000,
                                  content_types=CONTENT_TYPES)
    file = models.FileField("Plik", upload_to='documents/',
                            validators=[validate_file])
    description = models.CharField(
        "Opis", max_length=100, default="")
    category = models.CharField('Kategoria',  max_length=50,
                                choices=CATEGORY_CHOICES, default='Pozostałe')
    priority = models.IntegerField("Sortowanie (1-5)", default=2)
    show_as_new = models.BooleanField("Oznacz jako nowo dodany", default=False)

    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumenty'


    def __str__(self):
        return self.description
