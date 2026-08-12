from django.contrib import admin

from .models import Page, PageTranslation, PageType


class PageTranslationInline(admin.TabularInline):
    model = PageTranslation
    extra = 0


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["slug", "page_type", "status", "parent", "created_by", "is_deleted"]
    list_filter = ["page_type", "status", "is_deleted"]
    search_fields = ["slug"]
    inlines = [PageTranslationInline]

    def get_queryset(self, request):
        return Page.all_objects.all()


@admin.register(PageType)
class PageTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_system"]
    search_fields = ["name", "slug"]
