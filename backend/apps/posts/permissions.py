from rest_framework import permissions


class PostPermission(permissions.BasePermission):
    """Mirrors apps/pages/permissions.py — public read for published content,
    per-action permission for writes, superuser bypasses everything."""

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
            return user.has_perm("posts.publish_post")
        if action == "destroy":
            return user.has_perm("posts.delete_post")
        if action == "create":
            return user.has_perm("posts.add_post")
        if action in ("update", "partial_update", "duplicate", "restore"):
            return user.has_perm("posts.change_post")
        return True


class TaxonomyPermission(permissions.BasePermission):
    """Category/Tag — public read, `posts.change_post`-equivalent management gate.
    Reuses publish_post's holder set since taxonomy management sits with content
    editors, not a separate permission — CMS_BUILD_PROMPT.md §5.1."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.has_perm("posts.change_post")))
