from rest_framework import permissions


class PagePermission(permissions.BasePermission):
    """Public read for published content; writes need the matching per-action
    permission — CMS_BUILD_PROMPT.md §5.4 ("every feature/action defines its own
    permission"). Superuser bypasses everything (Django's native behavior)."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        action = getattr(view, "action", None)
        if action in ("publish", "unpublish"):
            return user.has_perm("pages.publish_page")
        if action == "destroy":
            return user.has_perm("pages.delete_page")
        if action == "create":
            return user.has_perm("pages.add_page")
        if action in ("update", "partial_update", "duplicate", "restore"):
            return user.has_perm("pages.change_page")
        return True
