from django.contrib import admin

from .models import BlockType, PageBlock, PostBlock


@admin.register(BlockType)
class BlockTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "is_system"]
    list_filter = ["category", "is_system"]
    search_fields = ["name", "slug"]


@admin.register(PageBlock)
class PageBlockAdmin(admin.ModelAdmin):
    list_display = ["page", "block_type", "parent", "order"]
    list_filter = ["block_type"]


@admin.register(PostBlock)
class PostBlockAdmin(admin.ModelAdmin):
    list_display = ["post", "block_type", "parent", "order"]
    list_filter = ["block_type"]
