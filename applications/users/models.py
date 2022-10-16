from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.db.models.fields import EmailField, DecimalField
from django.db.models import Q

from .managers import UserManager


class User(AbstractBaseUser):
    """User table model"""

    ROLE_CHOICES = (
        ("P", "Nie"),
        ("K", "Kierownik - przełożony"),
        ("T", "Instruktor, Zastępca Dyrektora"),
        ("S", "Dyrektor"),
        ("I", "Informatyk"),
    )

    username = models.CharField("Nazwa użytkownika", max_length=15, unique=True)
    email = models.EmailField("Email", null=True, blank=True)
    work_email = models.EmailField("Email służbowy", null=True, blank=True)
    first_name = models.CharField("Imię", max_length=30)
    last_name = models.CharField("Nazwisko", max_length=50)
    position = models.CharField("Stanowisko", max_length=50)
    position_addinfo = models.CharField(
        'Dopisek "sprz." w przypadku dwóch umów', max_length=50, blank=True
    )
    workplace = models.CharField("Dział/Filia", max_length=50, blank=True)
    role = models.CharField(
        "Stanowisko kierownicze", null=True, max_length=10, choices=ROLE_CHOICES
    )
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="user",
        on_delete=models.SET_NULL,
        verbose_name="przełożony",
    )
    working_hours = models.DecimalField(
        "Wymiar etatu", max_digits=3, decimal_places=2, default=1
    )
    annual_leave = models.IntegerField("Roczny wymiar urlopu", default=26)
    current_leave = models.IntegerField("Urlop (pozostało)", default=0)
    contract_end = models.DateField("Umowa do:", null=True, blank=True)
    is_staff = models.BooleanField("Dostęp do zakładki admin", default=False)
    is_active = models.BooleanField("Obecnie zatrudniony", default=True)
    is_superuser = models.BooleanField("Uprawnienia administratora", default=False)
    additional_info = models.CharField(
        "Dodatkowe informacje", blank=True, max_length=100
    )

    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        verbose_name = "Pracownik"
        verbose_name_plural = "Pracownicy"
        ordering = ["last_name", "first_name"]

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def __str__(self):
        return self.last_name + " " + self.first_name
