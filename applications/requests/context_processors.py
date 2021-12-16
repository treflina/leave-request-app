from django.contrib.auth.models import User
from .models import Request
from .managers import RequestManager

def number_requests_received(request):
    if request.user.is_authenticated:
        return {'requests_list': Request.objects.requests_received_counter(request.user)}
    else:
       return {'requests_list': 0}



