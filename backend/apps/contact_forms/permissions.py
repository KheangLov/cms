from rest_framework import permissions


class ContactSubmissionPermission(permissions.BasePermission):
    """Anyone can submit (it's a public contact form); only staff can read
    submissions back — this is a one-way mailbox, not a public message board."""

    def has_permission(self, request, view):
        if view.action == "create":
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff))
