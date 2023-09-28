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
