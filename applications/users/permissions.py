from rest_framework.permissions import BasePermission


class IsHRService(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.username == "hr_service"
        )
