from django.conf import settings
from django.db import models

from apps.common.constants import LOCALE_CHOICES
from apps.common.models import CONTAINER_WIDTH_CHOICES, SoftDeleteModel, TimestampedModel


class Category(TimestampedModel):
    """Hierarchical, like WordPress categories — CMS_BUILD_PROMPT.md §4."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class CategoryTranslation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="translations")
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["category", "locale"], name="unique_category_translation")
        ]

    def __str__(self):
        return f"{self.category.slug} ({self.locale})"


class Tag(TimestampedModel):
    """Flat, M2M with Post — CMS_BUILD_PROMPT.md §4."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TagTranslation(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="translations")
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tag", "locale"], name="unique_tag_translation")]

    def __str__(self):
        return f"{self.tag.slug} ({self.locale})"


class Post(SoftDeleteModel):
    """The actual chronological "blog article" entity — CMS_BUILD_PROMPT.md §5.1.
    featured_image FK to Media lands in Phase 3, once Media exists."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("scheduled", "Scheduled"),
        ("archived", "Archived"),
    ]

    slug = models.SlugField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    # CMS_BUILD_PROMPT.md §5.13 only specified this on Page — added here too since
    # blog posts are, if anything, the more commonly-commented content type.
    comments_enabled = models.BooleanField(default=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="posts"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="posts"
    )
    featured_image = models.ForeignKey(
        "media_library.Media", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    published_at = models.DateTimeField(null=True, blank=True)

    # Same "page settings" fields as Page — see apps/pages/models.py.
    container_width = models.CharField(max_length=20, choices=CONTAINER_WIDTH_CHOICES, default="default")
    background_color = models.CharField(max_length=30, blank=True)
    background_image_url = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug"], condition=models.Q(is_deleted=False), name="unique_post_slug_alive"
            ),
        ]
        permissions = [("publish_post", "Can publish posts")]
        indexes = [
            # The hottest read path — the blog-feed query — CMS_BUILD_PROMPT.md §6.1.
            models.Index(fields=["status", "published_at"], name="post_status_published_idx"),
        ]

    def __str__(self):
        return self.slug


class PostTranslation(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="translations")
    locale = models.CharField(max_length=8, choices=LOCALE_CHOICES)
    title = models.CharField(max_length=255)
    excerpt = models.CharField(max_length=500, blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "locale"], name="unique_post_translation_locale"),
        ]

    def __str__(self):
        return f"{self.post.slug} ({self.locale})"
