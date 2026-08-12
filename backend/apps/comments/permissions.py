from rest_framework import permissions


class CommentPermission(permissions.BasePermission):
    """CMS_BUILD_PROMPT.md §10.2 confirmed: comments require a logged-in account,
    no anonymous/guest comments. Public read is limited to approved comments —
    enforced in the viewset's get_queryset, not here."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if getattr(view, "action", None) in ("approve", "reject"):
            user = request.user
            return bool(user and user.is_authenticated and (user.is_superuser or user.has_perm("comments.moderate_comments")))
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user.is_superuser or obj.author_id == user.id or user.has_perm("comments.moderate_comments"))
