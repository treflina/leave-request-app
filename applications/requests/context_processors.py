from django.conf import settings
from .models import Request


def number_requests_received(request):
    """Count employees requests received by user that are still not accepted or
    rejected."""
    if request.user.is_authenticated:
        return {
            "requests_list": Request.objects.requests_received_counter(request.user)
        }
    else:
        return {"requests_list": 0}


def vapid_key(request):
    webpush_settings = getattr(settings, "WEBPUSH_SETTINGS", {})
    return {"vapid_key": webpush_settings.get("VAPID_PUBLIC_KEY")}
