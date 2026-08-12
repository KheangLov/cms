from django.db import models

from apps.common.models import SoftDeleteModel, TimestampedModel


class BlockType(TimestampedModel):
    """Registry entry for a reusable page-builder element — CMS_BUILD_PROMPT.md
    §4/§5.2. Extensible: a new block type is a registry row + a matching Vue
    component, no core rewrites. `prop_schema` drives the builder's properties
    panel generically instead of hardcoding a form per block type."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=50, default="content")
    icon = models.CharField(max_length=50, blank=True)
    prop_schema = models.JSONField(default=dict)
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class ContentBlock(SoftDeleteModel):
    """CMS_BUILD_PROMPT.md §4 — deliberately an abstract base with two concrete
    tables (PageBlock/PostBlock) below, not a GenericForeignKey: block content is
    the single most-read relation in the app, fetched on every public render, and
    GenericForeignKey can't be indexed/joined the way a normal FK can (§6.1).

    Soft-delete (§5.9) — removing a block in the builder is undoable, same as
    Page/Post/Media/Comment. Missed in the original Phase 4 pass (built on
    TimestampedModel); corrected here in Phase 5, soft-delete's own phase.

    `props` holds per-locale text directly, e.g. {"heading": {"en": "...", "km":
    "..."}, "ctaUrl": "/contact"} — no separate translation table per block
    instance, since block props are already a flexible JSON blob."""

    block_type = models.ForeignKey(BlockType, on_delete=models.PROTECT, related_name="+")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    order = models.PositiveIntegerField(default=0)
    props = models.JSONField(default=dict)

    class Meta:
        abstract = True
        ordering = ["order"]


class PageBlock(ContentBlock):
    page = models.ForeignKey("pages.Page", on_delete=models.CASCADE, related_name="blocks")

    class Meta(ContentBlock.Meta):
        indexes = [models.Index(fields=["page", "parent", "order"], name="pageblock_tree_idx")]


class PostBlock(ContentBlock):
    post = models.ForeignKey("posts.Post", on_delete=models.CASCADE, related_name="blocks")

    class Meta(ContentBlock.Meta):
        indexes = [models.Index(fields=["post", "parent", "order"], name="postblock_tree_idx")]
