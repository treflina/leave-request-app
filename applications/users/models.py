from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Users in the system."""

    ROLE_CHOICES = (
        ("P", _("no")),
        ("K", _("manager")),
        ("T", _("vice-director, instructor")),
        ("S", _("director")),
    )

    username = models.CharField(_("user name"), max_length=15, unique=True)
    email = models.EmailField("email", null=True, blank=True)
    work_email = models.EmailField(_("work email"), null=True, blank=True)
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=50)
    position = models.CharField(_("position"), max_length=50)
    position_addinfo = models.CharField(
        _("annotation in case of two contracts"), max_length=50, blank=True
    )
    workplace = models.CharField(_("department"), max_length=50, blank=True)
    role = models.CharField(
        _("management role"), null=True, max_length=10, choices=ROLE_CHOICES
    )
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="user",
        on_delete=models.SET_NULL,
        verbose_name=_("manager"),
    )
    working_hours = models.DecimalField(
        _("working hours"), max_digits=3, decimal_places=2, default=1
    )
    annual_leave = models.IntegerField(_("annual leave entitlement"), default=26)
    current_leave = models.IntegerField(_("current leave"), default=0)
    contract_end = models.DateField(_("contract end:"), null=True, blank=True)
    is_staff = models.BooleanField(_("access to admin bookmark"), default=False)
    is_active = models.BooleanField(_("currently employed"), default=True)
    is_superuser = models.BooleanField(_("superuser permissions"), default=False)
    additional_info = models.CharField(
        _("additional information"), blank=True, max_length=100
    )

    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        verbose_name = _("employee")
        verbose_name_plural = _("employees")
        ordering = ["last_name", "first_name"]
        
    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def __str__(self):
        return self.last_name + " " + self.first_name
