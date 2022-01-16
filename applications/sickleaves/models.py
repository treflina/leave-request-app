from django.db import models
from django.conf import settings

from .managers import SickleavesSearchManager


# Create your models here.
class Sickleave(models.Model):
    """Sickleave table model."""
    
    TYPE_CHOICES = (
        ('C', 'Chorobowe'),
        ('O', 'Opieka'),
        ('K', 'Kwarantanna'),
        ('I', 'Izolacja'),
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='osoba', related_name='sickemployee', default=""
    )
    type = models.CharField('Rodzaj',  max_length=10,
                            choices=TYPE_CHOICES, default='C')
    issue_date = models.DateField('Data wystawienia', null=True, blank=True)
    doc_number = models.CharField(
        'Nr dokumentu', max_length=20, null=True, blank=True)
    start_date = models.DateField('Od', null=True)
    end_date = models.DateField('Do', null=True)
    additional_info = models.CharField(
        'Dodatkowe informacje', max_length=50, blank=True)

    objects = SickleavesSearchManager()

    class Meta:
        verbose_name = 'Zwolnienie lekarskie'
        verbose_name_plural = 'Zwolnienia lekarskie'
        ordering = ['issue_date']

    def __str__(self):
        return self.employee.last_name + " " + self.employee.first_name + " " + str(self.start_date) + " " + str(self.end_date)
