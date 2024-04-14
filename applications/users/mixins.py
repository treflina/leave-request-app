from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect


def check_occupation_user(user):
    """Check if a user role is one of: staff, director, instructor
    or manager."""
    if user.is_anonymous:
        return False

    if user.role == "S" or user.role == "T" or user.role == "K":
        return True
    elif user.is_staff:
        return True
    else:
        return False


def check_staff(user):
    """Check if a user is staff or a director"""
    return not user.is_anonymous and (
        user.is_staff is True or user.role == 'S'
        )


class TopManagerPermisoMixin(LoginRequiredMixin):
    login_url = reverse_lazy("users_app:user-login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not check_occupation_user(request.user):
            return HttpResponseRedirect(reverse("users_app:user-login"))
        return super().dispatch(request, *args, **kwargs)


class StaffAndDirectorPermissionMixin(LoginRequiredMixin):
    login_url = reverse_lazy("users_app:user-login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not check_staff(request.user):
            return HttpResponseRedirect(reverse("users_app:user-login"))
        return super().dispatch(request, *args, **kwargs)
