from rest_framework import serializers

from .models import Category, CategoryTranslation, Post, PostTranslation, Tag, TagTranslation


class CategoryTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryTranslation
        fields = ["id", "locale", "name"]


class CategorySerializer(serializers.ModelSerializer):
    translations = CategoryTranslationSerializer(many=True, required=False)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "translations"]

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        category = Category.objects.create(**validated_data)
        for translation in translations_data:
            CategoryTranslation.objects.create(category=category, **translation)
        return category

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if translations_data is not None:
            instance.translations.all().delete()
            for translation in translations_data:
                CategoryTranslation.objects.create(category=instance, **translation)
        return instance


class TagTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagTranslation
        fields = ["id", "locale", "name"]


class TagSerializer(serializers.ModelSerializer):
    translations = TagTranslationSerializer(many=True, required=False)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "translations"]

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        tag = Tag.objects.create(**validated_data)
        for translation in translations_data:
            TagTranslation.objects.create(tag=tag, **translation)
        return tag

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if translations_data is not None:
            instance.translations.all().delete()
            for translation in translations_data:
                TagTranslation.objects.create(tag=instance, **translation)
        return instance


class PostTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostTranslation
        fields = ["id", "locale", "title", "excerpt", "meta_title", "meta_description"]


class PostSerializer(serializers.ModelSerializer):
    translations = PostTranslationSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "slug",
            "status",
            "category",
            "tags",
            "author",
            "featured_image",
            "published_at",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "translations",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at", "is_deleted", "deleted_at"]

    def create(self, validated_data):
        translations_data = validated_data.pop("translations", [])
        tags = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        if tags:
            post.tags.set(tags)
        for translation in translations_data:
            PostTranslation.objects.create(post=post, **translation)
        return post

    def update(self, instance, validated_data):
        translations_data = validated_data.pop("translations", None)
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        if translations_data is not None:
            instance.translations.all().delete()
            for translation in translations_data:
                PostTranslation.objects.create(post=instance, **translation)
        return instance


class PostDetailSerializer(PostSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
