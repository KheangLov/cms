from rest_framework import permissions, viewsets

from .models import Setting
from .serializers import SettingSerializer


class IsSuperuserOrManageSettings(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.has_perm("settings_app.manage_settings"))
        )


class SettingViewSet(viewsets.ModelViewSet):
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    permission_classes = [IsSuperuserOrManageSettings]
    lookup_field = "key"
    filterset_fields = ["category", "is_secret"]
    search_fields = ["key", "description"]
