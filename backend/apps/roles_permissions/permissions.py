from rest_framework import permissions


class IsSuperuserOrManageUsers(permissions.BasePermission):
    """Superuser bypasses everything natively; otherwise requires the manage_users
    permission — CMS_BUILD_PROMPT.md §5.4."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (user.is_superuser or user.has_perm("users.manage_users"))
        )
