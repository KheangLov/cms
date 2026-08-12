from rest_framework import permissions


class BlockPermission(permissions.BasePermission):
    """Blocks are page/post content — same gate as editing the parent Page/Post
    (change_page or change_post), not a separate permission. Public read for
    everyone (blocks of a published page are public content)."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return user.has_perm("pages.change_page") or user.has_perm("posts.change_post")
