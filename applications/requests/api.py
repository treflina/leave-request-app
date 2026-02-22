from collections import defaultdict
from django.db.models import Q
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.decorators import (
        api_view,
        authentication_classes,
        permission_classes
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from applications.users.permissions import IsHRService
from .models import Request
# , LeaveApiAudit

User = get_user_model()


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsHRService])
def hr_leave_month_api(request, year, month):
    if not (1 <= month <= 12):
        return Response(
            {"error_code": "INVALID_MONTH"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)

    qs = Request.objects.filter(
        status="zaakceptowany",
    ).filter(
        Q(start_date__lte=month_end, end_date__gte=month_start)
        | Q(work_date__gte=month_start, work_date__lte=month_end)
    ).select_related("author")

    result = defaultdict(dict)

    for r in qs:
        user = r.author.username

        if r.leave_type in ("WS", "WN") and r.work_date:
            if month_start <= r.work_date <= month_end:
                result[user][r.work_date.isoformat()] = "P"

        if r.start_date and r.end_date:
            current = max(r.start_date, month_start)
            end = min(r.end_date, month_end)
            while current <= end:
                result[user][current.isoformat()] = r.leave_type
                current += timedelta(days=1)

    # LeaveApiAudit.objects.create(
    #     actor=request.user,
    #     employee=None,
    #     year=year,
    #     month=month,
    #     ip=request.META.get("REMOTE_ADDR"),
    # )

    return Response(
        {
            "year": year,
            "month": month,
            "employees": result,
        }
    )
