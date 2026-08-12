from rest_framework import serializers

from .models import BlockType, PageBlock, PostBlock


class BlockTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockType
        fields = ["id", "name", "slug", "category", "icon", "prop_schema", "is_system"]


class PageBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageBlock
        fields = [
            "id", "page", "block_type", "parent", "order", "props",
            "created_at", "updated_at", "is_deleted", "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted", "deleted_at"]


class PostBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostBlock
        fields = [
            "id", "post", "block_type", "parent", "order", "props",
            "created_at", "updated_at", "is_deleted", "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted", "deleted_at"]


class PageBlockTreeSerializer(serializers.ModelSerializer):
    """Recursive — used for public rendering (§5.2: same components render the
    builder preview and the public page, both need the same nested shape)."""

    block_type = BlockTypeSerializer(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = PageBlock
        fields = ["id", "block_type", "order", "props", "children"]

    def get_children(self, obj):
        children = obj.children.select_related("block_type").order_by("order")
        return PageBlockTreeSerializer(children, many=True).data


class PostBlockTreeSerializer(serializers.ModelSerializer):
    block_type = BlockTypeSerializer(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        model = PostBlock
        fields = ["id", "block_type", "order", "props", "children"]

    def get_children(self, obj):
        children = obj.children.select_related("block_type").order_by("order")
        return PostBlockTreeSerializer(children, many=True).data
