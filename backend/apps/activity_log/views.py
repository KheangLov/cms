from rest_framework import permissions, viewsets

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class IsStaffOrSuperuser(permissions.BasePermission):
    """Audit trail — CMS_BUILD_PROMPT.md §5.10 calls this "a read-heavy audit feed,
    not user-facing content," so staff-only, not gated by a bespoke permission."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff))


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.select_related("actor")
    serializer_class = ActivityLogSerializer
    permission_classes = [IsStaffOrSuperuser]
    filterset_fields = ["verb", "target_type", "actor"]
    search_fields = ["target_repr"]
    ordering_fields = ["timestamp"]
