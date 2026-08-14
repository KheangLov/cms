from django.db import migrations

# General-purpose blocks — none of these are hospital-specific despite that being
# the first use case; a feature grid, an urgent-contact banner, and a card list are
# common enough patterns for any content-driven site. Links are plain URL strings
# (same trade-off as HeroBlock.ctaUrl), not page-id FKs — Navbar/Footer needed
# live-resolved page links because they're site-wide and outlive any one page's
# slug, but a block embedded in a single page's own content doesn't need that.
BLOCK_TYPES = [
    {
        "name": "Feature Grid",
        "slug": "feature-grid",
        "category": "content",
        "icon": "mdi-view-grid-plus",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {
                    "key": "items",
                    "type": "list",
                    "label": "Grid items",
                    "itemFields": [
                        {"key": "icon", "type": "text", "label": "Icon name (e.g. solar:heart-bold-duotone)"},
                        {"key": "label", "type": "text", "translatable": True, "label": "Label"},
                        {"key": "url", "type": "text", "label": "Link URL"},
                    ],
                },
            ]
        },
    },
    {
        "name": "Callout",
        "slug": "callout",
        "category": "content",
        "icon": "mdi-bullhorn",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {"key": "subheading", "type": "text", "translatable": True, "label": "Subheading"},
                {"key": "phone", "type": "text", "label": "Phone number"},
                {"key": "phoneSecondary", "type": "text", "label": "Secondary phone number (optional)"},
                {"key": "ctaLabel", "type": "text", "translatable": True, "label": "Button label"},
                {"key": "ctaUrl", "type": "text", "label": "Button URL"},
            ]
        },
    },
    {
        "name": "Cards",
        "slug": "cards",
        "category": "content",
        "icon": "mdi-cards-outline",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {
                    "key": "cards",
                    "type": "list",
                    "label": "Cards",
                    "itemFields": [
                        {"key": "title", "type": "text", "translatable": True, "label": "Title"},
                        {"key": "body", "type": "text", "translatable": True, "label": "Body"},
                        {"key": "url", "type": "text", "label": "Link URL (optional)"},
                    ],
                },
            ]
        },
    },
]


def seed(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    for block in BLOCK_TYPES:
        BlockType.objects.get_or_create(slug=block["slug"], defaults=block)


def unseed(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug__in=[b["slug"] for b in BLOCK_TYPES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("blocks", "0005_seed_navbar_footer_block_types"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
