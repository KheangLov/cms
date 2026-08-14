from django.conf import settings
from django.db import models

from apps.common.constants import LOCALE_CHOICES
from apps.common.models import CONTAINER_WIDTH_CHOICES, SoftDeleteModel, TimestampedModel


class PageType(TimestampedModel):
    """CMS_BUILD_PROMPT.md §4 — Landing Page, Blog, About, Contact, Quiz, Survey,
    Custom… An extensible model (not a hardcoded enum) so new types can be added
    through the admin later without a code migration."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_system = models.BooleanField(default=False)

    # Empty (the default for every page type today) means unrestricted — every
    # block type is available, the pre-existing behavior. A non-empty set scopes
    # the builder's palette (and is enforced server-side in PageBlockSerializer)
    # to just these block types, so e.g. a "Contact" page type could be limited to
    # the blocks that actually make sense on a contact page.
    allowed_block_types = models.ManyToManyField(
        "blocks.BlockType", blank=True, related_name="allowed_for_page_types"
    )

    # Blocks to auto-create on a *new* page of this type — a starting point an
    # editor edits from, not a template that stays in sync afterwards. Each
    # entry: {"block_type": "<slug>", "props": {...}, "children": [...]}
    # (children nest the same shape, for e.g. Columns' child blocks). Applied
    # once, at creation time, in PageViewSet.perform_create — never touches an
    # existing page, and duplicate()/update() don't go through that path so
    # they're unaffected.
    default_blocks = models.JSONField(default=list, blank=True)

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

    # Per-page presentation, independent of block content — a "page settings"
    # concern, not a block. `background_image_url` is freeform text rather than a
    # Media FK, same trade-off HeroBlock.backgroundImageUrl already made: no
    # picker UI needed, and an admin can point it at anything.
    container_width = models.CharField(max_length=20, choices=CONTAINER_WIDTH_CHOICES, default="default")
    background_color = models.CharField(max_length=30, blank=True)
    background_image_url = models.CharField(max_length=500, blank=True)

    class Meta:
        # Without this, paginated Page lists are ordered only by whatever Postgres
        # happens to return, so rows can repeat or be skipped across page boundaries
        # (DRF warns about exactly this: UnorderedObjectListWarning). -id is a
        # tiebreaker for rows sharing a created_at. Post/Media/Comment already set
        # their own ordering; Page was the only SoftDeleteModel missing it.
        ordering = ["-created_at", "-id"]
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
        # The `seen` guard is deliberate: PageSerializer rejects parent cycles, but
        # this walk must not hang on a row that predates that validation or was
        # written directly (shell/fixture/SQL). Without it a self-parented page spins
        # forever while `segments` grows unboundedly — one bad row would take out a
        # worker thread on any request that renders a page path.
        segments = [self.slug]
        seen = {self.pk}
        node = self.parent
        while node is not None and node.pk not in seen:
            seen.add(node.pk)
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
