from django.contrib import admin

from .models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["key", "category", "is_secret", "updated_at"]
    list_filter = ["category", "is_secret"]
    search_fields = ["key", "description"]
