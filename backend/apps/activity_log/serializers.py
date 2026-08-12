from rest_framework import serializers

from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "actor",
            "actor_email",
            "verb",
            "target_type",
            "target_id",
            "target_repr",
            "diff",
            "ip_address",
            "timestamp",
        ]
