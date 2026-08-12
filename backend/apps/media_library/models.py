from django.conf import settings
from django.db import models

from apps.common.models import SoftDeleteModel


class Media(SoftDeleteModel):
    """CMS_BUILD_PROMPT.md §5.3 — original + optimized/thumbnail variants, generated
    asynchronously by apps/media_library/tasks.py so uploads never block the request."""

    PROCESSING_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("skipped", "Skipped"),  # non-image files — no thumbnails to generate
        ("failed", "Failed"),
    ]

    file = models.FileField(upload_to="uploads/%Y/%m/")
    thumbnail_small = models.FileField(upload_to="thumbnails/small/%Y/%m/", null=True, blank=True)
    thumbnail_medium = models.FileField(upload_to="thumbnails/medium/%Y/%m/", null=True, blank=True)
    optimized = models.FileField(upload_to="optimized/%Y/%m/", null=True, blank=True)

    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    processing_status = models.CharField(max_length=20, choices=PROCESSING_CHOICES, default="pending")

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="uploaded_media"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_filename
