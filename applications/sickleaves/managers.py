from django.db import models
from django.db.models import Q


class SickleavesSearchManager(models.Manager):
    """Search manager for Sickleave Model"""

    def sickleaves_search(self, kword):
        result = self.filter(
            Q(employee__last_name__icontains=kword)
            | Q(employee__first_name__icontains=kword)
        )
        return result
