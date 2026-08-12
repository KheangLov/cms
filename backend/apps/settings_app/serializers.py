from rest_framework import serializers

from .models import Setting


class SettingSerializer(serializers.ModelSerializer):
    # `value` is a Python property (encrypts/decrypts through `raw_value`), not a real
    # model field, so it's declared explicitly and create/update are overridden below —
    # the default ModelSerializer.create() would pass value= straight into Setting(...)
    # and Django would reject it as an unknown field.
    value = serializers.JSONField()

    class Meta:
        model = Setting
        fields = ["id", "key", "value", "category", "is_secret", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        value = validated_data.pop("value")
        instance = Setting(**validated_data)
        instance.value = value
        instance.save()
        return instance

    def update(self, instance, validated_data):
        value = validated_data.pop("value", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if value is not None:
            instance.value = value
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_secret:
            # Write-only in practice — CMS_BUILD_PROMPT.md §5.8: "never echoed back
            # in plaintext after save." `has_value` lets the UI show "configured"
            # without ever exposing the actual key.
            data["value"] = None
            data["has_value"] = bool(instance.raw_value)
        return data
