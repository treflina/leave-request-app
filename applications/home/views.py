from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView 

from applications.users.models import User

class HomePage(LoginRequiredMixin, TemplateView):
    
    template_name = "home/index.html"
    model =User 
    login_url = reverse_lazy('users_app:user-login')
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.working_hours < 1:
            context['part'] = True
        if self.request.user.current_leave == 1:
            context['onedayleft'] = True
        if self.request.user.role == "S":
            context['show_director'] = True
        if self.request.user.role == "T" or self.request.user.role == "K":
            context['show_manager'] = True
        return context

   