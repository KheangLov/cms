from django.db import migrations

# Adds an optional per-card image (e.g. a doctor's avatar) to the Cards block —
# CardsBlock.vue already gracefully skips rendering an image when absent, so
# every card created before this migration keeps working unchanged.
NEW_SCHEMA = {
    "fields": [
        {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
        {
            "key": "cards",
            "type": "list",
            "label": "Cards",
            "itemFields": [
                {"key": "title", "type": "text", "translatable": True, "label": "Title"},
                {"key": "body", "type": "text", "translatable": True, "label": "Body"},
                {"key": "imageUrl", "type": "text", "label": "Image URL (optional)"},
                {"key": "url", "type": "text", "label": "Link URL (optional)"},
            ],
        },
    ]
}

OLD_SCHEMA = {
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
}


def upgrade(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug="cards").update(prop_schema=NEW_SCHEMA)


def downgrade(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug="cards").update(prop_schema=OLD_SCHEMA)


class Migration(migrations.Migration):
    dependencies = [
        ("blocks", "0009_seed_contact_form_map_block_types"),
    ]

    operations = [
        migrations.RunPython(upgrade, downgrade),
    ]
