from django.conf import settings
from django.db import models

from apps.common.models import SoftDeleteModel, TimestampedModel

LOCALE_CHOICES = [("en", "English"), ("km", "Khmer")]


class PageType(TimestampedModel):
    """CMS_BUILD_PROMPT.md §4 — Landing Page, Blog, About, Contact, Quiz, Survey,
    Custom… An extensible model (not a hardcoded enum) so new types can be added
    through the admin later without a code migration."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Page(SoftDeleteModel):
    """Static/structural content: Landing, About, Contact, Custom, plus the
    Quiz/Survey/Blog "container" pages — CMS_BUILD_PROMPT.md §5.1."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("scheduled", "Scheduled"),
        ("archived", "Archived"),
    ]

    slug = models.SlugField(max_length=255)
    page_type = models.ForeignKey(PageType, on_delete=models.PROTECT, related_name="pages")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    comments_enabled = models.BooleanField(default=True)
    publish_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "slug"],
                condition=models.Q(parent__isnull=False, is_deleted=False),
                name="unique_page_slug_per_parent_alive",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=models.Q(parent__isnull=True, is_deleted=False),
                name="unique_root_page_slug_alive",
            ),
        ]
        permissions = [("publish_page", "Can publish pages")]
        indexes = [
            models.Index(fields=["status", "page_type"], name="page_status_type_idx"),
        ]

    def __str__(self):
        return self.slug

    def full_path(self):
        segments = [self.slug]
        node = self.parent
        while node is not None:
            segments.append(node.slug)
            node = node.parent
        return "/".join(reversed(segments))


class PageTranslation(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="translations")
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES)
    title = models.CharField(max_length=255)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)
    og_image = models.ForeignKey(
        "media_library.Media", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["page", "locale"], name="unique_page_translation_locale"),
        ]

    def __str__(self):
        return f"{self.page.slug} ({self.locale})"
