from django.contrib import admin

from .models import Category, CategoryTranslation, Post, PostTranslation, Tag, TagTranslation


class PostTranslationInline(admin.TabularInline):
    model = PostTranslation
    extra = 0


class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = 0


class TagTranslationInline(admin.TabularInline):
    model = TagTranslation
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["slug", "status", "category", "author", "published_at", "is_deleted"]
    list_filter = ["status", "category", "is_deleted"]
    search_fields = ["slug"]
    inlines = [PostTranslationInline]

    def get_queryset(self, request):
        return Post.all_objects.all()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent"]
    search_fields = ["name", "slug"]
    inlines = [CategoryTranslationInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    inlines = [TagTranslationInline]
