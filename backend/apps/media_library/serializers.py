from rest_framework import serializers

from .models import Media


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            "id",
            "file",
            "thumbnail_small",
            "thumbnail_medium",
            "optimized",
            "original_filename",
            "mime_type",
            "size_bytes",
            "width",
            "height",
            "processing_status",
            "uploaded_by",
            "created_at",
            "is_deleted",
        ]
        read_only_fields = [
            "id",
            "thumbnail_small",
            "thumbnail_medium",
            "optimized",
            "original_filename",
            "mime_type",
            "size_bytes",
            "width",
            "height",
            "processing_status",
            "uploaded_by",
            "created_at",
            "is_deleted",
        ]
