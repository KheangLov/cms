from django.db import migrations

# WordPress-inspired "Latest Posts" block — lets a Page (or Post) embed a list of
# Posts, either automatically (by category + count) or manually curated (specific
# post ids). No bespoke picker UI: `postIds` is a `list`-type field, same as
# Swiper's `slides` in 0002 — edited via the builder's existing raw-JSON escape
# hatch rather than a one-off field type.
BLOCK_TYPE = {
    "name": "Posts",
    "slug": "posts",
    "category": "content",
    "icon": "mdi-post",
    "is_system": True,
    "prop_schema": {
        "fields": [
            {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
            {"key": "categorySlug", "type": "text", "label": "Category slug (blank = any)"},
            {"key": "count", "type": "number", "label": "Number of posts (latest mode)", "default": 3},
            {
                "key": "postIds",
                "type": "list",
                "label": "Specific post IDs (optional — overrides category/count)",
            },
        ]
    },
}


def seed(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.get_or_create(slug=BLOCK_TYPE["slug"], defaults=BLOCK_TYPE)


def unseed(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug=BLOCK_TYPE["slug"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("blocks", "0003_pageblock_deleted_at_pageblock_deleted_by_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
