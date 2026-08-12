from rest_framework import permissions


class MediaPermission(permissions.BasePermission):
    """CMS_BUILD_PROMPT.md §5.4: "Upload media — Admin ✅, Editor ✅, User ✅ (own
    only)." Any authenticated user may upload and read; only the uploader, a
    superuser, or someone with the standard change/delete permission may modify or
    remove someone else's upload."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if user.is_superuser or obj.uploaded_by_id == user.id:
            return True
        if request.method == "DELETE":
            return user.has_perm("media_library.delete_media")
        return user.has_perm("media_library.change_media")
