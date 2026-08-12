from django.contrib.auth.models import Group, Permission
from rest_framework import serializers


class PermissionSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(source="content_type.model", read_only=True)
    app_label = serializers.CharField(source="content_type.app_label", read_only=True)

    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type", "app_label"]


class RoleSerializer(serializers.ModelSerializer):
    """"Role" in CMS_BUILD_PROMPT.md §4/§5.4 — a named bundle of permissions, built
    directly on Django's Group model rather than reinventing it."""

    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]
