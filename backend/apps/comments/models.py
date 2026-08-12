from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.common.models import SoftDeleteModel


class Comment(SoftDeleteModel):
    """CMS_BUILD_PROMPT.md §5.13 — attaches to a Page or a Post via
    GenericForeignKey. This is the deliberate exception noted in §4: comments are
    fetched far less often than block content (on-demand per page view, not on
    every render of every block), so a GenericForeignKey's query cost is fine here
    where it wouldn't be for PageBlock/PostBlock."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    body = models.TextField()

    STATUS_CHOICES = [("pending", "Pending"), ("approved", "Approved"), ("spam", "Spam")]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["content_type", "object_id"], name="comment_target_idx")]
        permissions = [("moderate_comments", "Can moderate comments")]

    def __str__(self):
        return f"{self.author} on {self.content_type}#{self.object_id}"
