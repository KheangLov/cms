from django.db import migrations

# Site-wide chrome, modeled as ordinary blocks (same registry, same builder UI as
# every other block type) rather than a bespoke Menu/Header model — a `links` list
# of {label, pageId, url} lets an editor point a menu item at either a live Page
# (resolved to its current full_path server-side, see ResolveView/site-chrome
# view) or a raw external URL, without inventing a new CRUD subsystem.
BLOCK_TYPES = [
    {
        "name": "Navbar",
        "slug": "navbar",
        "category": "layout",
        "icon": "mdi-view-headline",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "logoText", "type": "text", "translatable": True, "label": "Site name"},
                {"key": "logoUrl", "type": "text", "label": "Logo image URL (optional)"},
                {
                    "key": "links",
                    "type": "list",
                    "label": "Menu links",
                    "itemFields": [
                        {"key": "label", "type": "text", "translatable": True, "label": "Label"},
                        {"key": "pageId", "type": "number", "label": "Linked page ID (optional)"},
                        {"key": "url", "type": "text", "label": "URL (used if no page ID)"},
                    ],
                },
            ]
        },
    },
    {
        "name": "Footer",
        "slug": "footer",
        "category": "layout",
        "icon": "mdi-page-layout-footer",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {
                    "key": "links",
                    "type": "list",
                    "label": "Menu links",
                    "itemFields": [
                        {"key": "label", "type": "text", "translatable": True, "label": "Label"},
                        {"key": "pageId", "type": "number", "label": "Linked page ID (optional)"},
                        {"key": "url", "type": "text", "label": "URL (used if no page ID)"},
                    ],
                },
                {"key": "contactEmail", "type": "text", "label": "Contact email"},
                {"key": "contactPhone", "type": "text", "label": "Contact phone"},
                {"key": "contactAddress", "type": "textarea", "label": "Contact address"},
                {"key": "copyrightText", "type": "text", "translatable": True, "label": "Copyright line"},
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
        ("blocks", "0004_seed_posts_block_type"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
