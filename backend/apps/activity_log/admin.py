from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "actor", "verb", "target_type", "target_id", "target_repr"]
    list_filter = ["verb", "target_type"]
    search_fields = ["target_repr"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
