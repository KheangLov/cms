from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "locale_preference",
            "theme_preference",
            "is_2fa_enabled",
            "is_superuser",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "is_superuser", "is_staff", "date_joined"]


class UserAdminSerializer(serializers.ModelSerializer):
    """Used by UserViewSet (manage_users-gated) — unlike UserSerializer (self-service
    /auth/me/), this exposes group membership and active status for administration."""

    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    groups_detail = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_2fa_enabled",
            "groups",
            "groups_detail",
            "date_joined",
            "password",
        ]
        read_only_fields = ["id", "is_2fa_enabled", "date_joined"]

    def get_groups_detail(self, obj):
        return [{"id": g.id, "name": g.name} for g in obj.groups.all()]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", [])
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
        if groups:
            user.groups.set(groups)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if groups is not None:
            instance.groups.set(groups)
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
