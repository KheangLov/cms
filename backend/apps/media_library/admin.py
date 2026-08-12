from django.contrib import admin

from .models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "mime_type", "processing_status", "uploaded_by", "created_at", "is_deleted"]
    list_filter = ["mime_type", "processing_status", "is_deleted"]
    search_fields = ["original_filename"]

    def get_queryset(self, request):
        return Media.all_objects.all()
