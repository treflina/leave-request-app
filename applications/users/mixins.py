from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect


def check_occupation_user(user, role):
    if role == "S" or role == "T" or role == "K":
        return True
    elif user.is_staff:
        return True
    else:
        return False


class TopManagerPermisoMixin(LoginRequiredMixin):
    login_url = reverse_lazy("users_app:user-login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not check_occupation_user(request.user, request.user.role):
            return HttpResponseRedirect(reverse("users_app:user-login"))
        return super().dispatch(request, *args, **kwargs)
