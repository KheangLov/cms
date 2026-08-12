from django.db import migrations

# CMS_BUILD_PROMPT.md §5.2 — starter catalog. Extensible: more block types are added
# later as further migrations, not code changes to core page/post logic.
BLOCK_TYPES = [
    {
        "name": "Hero Section",
        "slug": "hero",
        "category": "content",
        "icon": "mdi-image-text",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {"key": "subheading", "type": "text", "translatable": True, "label": "Subheading"},
                {"key": "backgroundImageUrl", "type": "text", "label": "Background Image URL"},
                {"key": "ctaLabel", "type": "text", "translatable": True, "label": "Button Label"},
                {"key": "ctaUrl", "type": "text", "label": "Button URL"},
            ]
        },
    },
    {
        "name": "Text Section",
        "slug": "text-section",
        "category": "content",
        "icon": "mdi-text-box",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {"key": "body", "type": "textarea", "translatable": True, "label": "Body"},
            ]
        },
    },
    {
        "name": "Swiper",
        "slug": "swiper",
        "category": "media",
        "icon": "mdi-view-carousel",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {
                    "key": "slides",
                    "type": "list",
                    "label": "Slides",
                    "itemFields": [
                        {"key": "imageUrl", "type": "text", "label": "Image URL"},
                        {"key": "caption", "type": "text", "translatable": True, "label": "Caption"},
                    ],
                }
            ]
        },
    },
    {
        "name": "Columns",
        "slug": "columns",
        "category": "layout",
        "icon": "mdi-view-column",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "columnCount", "type": "number", "label": "Columns", "default": 2},
            ]
        },
    },
]


def seed_block_types(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    for block in BLOCK_TYPES:
        BlockType.objects.get_or_create(slug=block["slug"], defaults=block)


def unseed_block_types(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug__in=[b["slug"] for b in BLOCK_TYPES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("blocks", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_block_types, unseed_block_types),
    ]
