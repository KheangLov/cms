from rest_framework import serializers

from .models import Page, PageTranslation, PageType


class PageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageType
        fields = ["id", "name", "slug", "description", "is_system"]
        read_only_fields = ["is_system"]


class PageTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageTranslation
        fields = ["id", "locale", "title", "meta_title", "meta_description", "og_image_url"]


class PageSerializer(serializers.ModelSerializer):
    translations = PageTranslationSerializer(many=True, required=False)

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
            "created_by",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "translations",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "is_deleted", "deleted_at"]

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
    full_path = serializers.CharField(read_only=True)

    class Meta(PageSerializer.Meta):
        fields = PageSerializer.Meta.fields + ["full_path"]
