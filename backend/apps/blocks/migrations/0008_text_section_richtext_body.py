from django.db import migrations

# Upgrades Text Section's `body` field from plain textarea to a rich-text
# editor (Tiptap in the admin builder) — content is now stored as HTML rather
# than plain text. TextSectionBlock.vue renders it with v-html but keeps
# white-space: pre-line, so already-published plain-text bodies (which have no
# HTML tags) still render exactly as before — nothing needs a data migration.
NEW_SCHEMA = {
    "fields": [
        {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
        {"key": "body", "type": "richtext", "translatable": True, "label": "Body"},
    ]
}

OLD_SCHEMA = {
    "fields": [
        {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
        {"key": "body", "type": "textarea", "translatable": True, "label": "Body"},
    ]
}


def upgrade(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug="text-section").update(prop_schema=NEW_SCHEMA)


def downgrade(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug="text-section").update(prop_schema=OLD_SCHEMA)


class Migration(migrations.Migration):
    dependencies = [
        ("blocks", "0007_footer_columns_schema"),
    ]

    operations = [
        migrations.RunPython(upgrade, downgrade),
    ]
