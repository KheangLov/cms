from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.pages.models import Page
from apps.posts.models import Post

from .models import Comment

TARGET_MODELS = {"page": (Page, "pages", "page"), "post": (Post, "posts", "post")}


class CommentSerializer(serializers.ModelSerializer):
    target_type = serializers.ChoiceField(choices=list(TARGET_MODELS), write_only=True)
    target_id = serializers.IntegerField(write_only=True)
    resolved_target_type = serializers.SerializerMethodField(read_only=True)
    author_email = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "target_type",
            "target_id",
            "resolved_target_type",
            "object_id",
            "author",
            "author_email",
            "parent",
            "body",
            "status",
            "created_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "object_id", "author", "status", "created_at", "is_deleted"]

    def get_resolved_target_type(self, obj):
        return obj.content_type.model

    def get_author_email(self, obj):
        return obj.author.email if obj.author_id else None

    def validate(self, attrs):
        target_type = attrs.get("target_type")
        target_id = attrs.get("target_id")
        if target_type and target_id:
            model, _, _ = TARGET_MODELS[target_type]
            try:
                target = model.objects.get(pk=target_id)
            except model.DoesNotExist as exc:
                raise serializers.ValidationError({"target_id": "Not found."}) from exc
            if not target.comments_enabled:
                raise serializers.ValidationError("Comments are disabled for this content.")
        return attrs

    def create(self, validated_data):
        target_type = validated_data.pop("target_type")
        target_id = validated_data.pop("target_id")
        _, app_label, model_name = TARGET_MODELS[target_type]
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        return Comment.objects.create(content_type=content_type, object_id=target_id, **validated_data)
