from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets

from .permissions import IsSuperuserOrManageUsers
from .serializers import PermissionSerializer, RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().prefetch_related("permissions").order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsSuperuserOrManageUsers]
    filterset_fields = ["name"]
    search_fields = ["name"]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — permissions themselves are defined by the codebase (model Meta),
    not created through the API; only their assignment to Roles is editable."""

    queryset = Permission.objects.all().select_related("content_type").order_by("content_type__app_label", "codename")
    serializer_class = PermissionSerializer
    permission_classes = [IsSuperuserOrManageUsers]
    filterset_fields = ["content_type__app_label"]
    search_fields = ["codename", "name"]
