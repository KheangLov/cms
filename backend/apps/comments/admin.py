from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "content_type", "object_id", "status", "created_at", "is_deleted"]
    list_filter = ["status", "content_type", "is_deleted"]
    search_fields = ["body"]

    def get_queryset(self, request):
        return Comment.all_objects.all()
