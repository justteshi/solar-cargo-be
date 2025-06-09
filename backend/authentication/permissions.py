from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return hasattr(user, 'profile') and user.profile.role == 'admin'


class IsBasicUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return hasattr(user, 'profile') and user.profile.role == 'basic'
