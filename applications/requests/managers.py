from django.db import models
from django.db.models import Q


class RequestManager(models.Manager):
    """Managers for Request Model"""

    # manager for listing employees requests
    def requests_to_accept(self, user):
        result = self.filter(Q(send_to_person=user) & Q(status="oczekujący")).order_by(
            "created"
        )
        return result

    # managers for listing user requests
    def user_requests_holiday(self, user):
        result = self.filter(Q(author__id=user.id) & Q(leave_type="W")).order_by(
            "-created"
        )
        return result

    def user_requests_other(self, user):
        result = self.filter(Q(author__id=user.id) & (~Q(leave_type="W"))).order_by(
            "-created"
        )
        return result

    def requests_received_counter(self, user):
        """Manager that counts received requests with status 'to accept'."""
        employees_requests_received_count = self.filter(
            Q(send_to_person=user) & Q(status="oczekujący")
        ).count()
        return employees_requests_received_count

        # symbols = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "10+"]

        # if employees_requests_received_count > 10:
        #     return "10+"
        # return symbols[employees_requests_received_count]
