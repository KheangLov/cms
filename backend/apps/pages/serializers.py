from rest_framework import serializers

from apps.blocks.serializers import PageBlockTreeSerializer

from .models import Page, PageTranslation, PageType


class PageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageType
        fields = ["id", "name", "slug", "description", "is_system", "allowed_block_types", "default_blocks"]
        read_only_fields = ["is_system"]


class PageTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageTranslation
        fields = ["id", "locale", "title", "meta_title", "meta_description", "og_image"]


class PageSerializer(serializers.ModelSerializer):
    translations = PageTranslationSerializer(many=True, required=False)
    # Needed by the admin list (not just retrieve/resolve) so a "Open" link can
    # be built for nested pages without the client re-deriving the parent walk.
    full_path = serializers.CharField(read_only=True)

    class Meta:
        model = Page
        fields = [
            "id",
            "slug",
            "page_type",
            "status",
            "parent",
            "comments_enabled",
            "publish_at",
            "container_width",
            "background_color",
            "background_image_url",
            "created_by",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "translations",
            "full_path",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "is_deleted", "deleted_at"]

    def validate_parent(self, value):
        """Reject parent cycles.

        `parent` is a plain FK field, so without this any page id is accepted —
        including the page's own. A cycle silently un-roots the page (ResolveView
        walks down from parent=None, so it stops resolving) and makes
        Page.full_path() loop forever.
        """
        if value is None:
            return value
        if self.instance is None:
            # On create the page has no pk yet, so it cannot be part of a cycle.
            return value
        if value.pk == self.instance.pk:
            raise serializers.ValidationError("A page cannot be its own parent.")

        # Walk up from the proposed parent: if we reach this page, the proposed
        # parent is one of its descendants and linking them would close a loop.
        # `seen` also stops the walk on data that is already cyclic.
        seen = set()
        node = value
        while node is not None and node.pk not in seen:
            if node.pk == self.instance.pk:
                raise serializers.ValidationError(
                    "That page is a descendant of this one — it cannot also be its parent."
                )
            seen.add(node.pk)
            node = node.parent
        return value

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        page = Page.objects.create(**validated_data)
        for translation in translations_data:
            PageTranslation.objects.create(page=page, **translation)
        return page

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if translations_data is not None:
            instance.translations.all().delete()
            for translation in translations_data:
                PageTranslation.objects.create(page=instance, **translation)
        return instance


class PageDetailSerializer(PageSerializer):
    """Nests page_type fully rather than just its id — used for retrieve/resolve,
    where the client needs the full object, not another round trip."""

    page_type = PageTypeSerializer(read_only=True)
    blocks = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta(PageSerializer.Meta):
        fields = PageSerializer.Meta.fields + ["blocks", "comments"]

    def get_blocks(self, obj):
        top_level = obj.blocks.filter(parent__isnull=True).select_related("block_type").order_by("order")
        return PageBlockTreeSerializer(top_level, many=True).data

    def get_comments(self, obj):
        from apps.comments.serializers import CommentPublicSerializer
        from apps.comments.utils import approved_comments_for

        if not obj.comments_enabled:
            return []
        return CommentPublicSerializer(approved_comments_for(obj), many=True).data
