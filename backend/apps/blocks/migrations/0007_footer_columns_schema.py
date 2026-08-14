from django.db import migrations

# Upgrades the Footer BlockType's prop_schema from a single flat `links` list to
# multiple named columns (heading + links each) plus a logo and social links —
# "fully customizable" footer per the admin's request, closer to what a real
# site's footer usually needs (several sections, not one flat menu).
# Existing Footer block *instances* keep whatever props they already have;
# FooterBlock.vue supports both the old flat `links` shape and the new
# `columns` shape so nothing already published breaks.
NEW_SCHEMA = {
    "fields": [
        {"key": "logoText", "type": "text", "translatable": True, "label": "Site name"},
        {"key": "logoUrl", "type": "text", "label": "Logo image URL (optional)"},
        {
            "key": "columns",
            "type": "list",
            "label": "Link columns",
            "itemFields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Column heading"},
                {
                    "key": "links",
                    "type": "list",
                    "label": "Links",
                    "itemFields": [
                        {"key": "label", "type": "text", "translatable": True, "label": "Label"},
                        {"key": "url", "type": "text", "label": "URL"},
                    ],
                },
            ],
        },
        {
            "key": "socialLinks",
            "type": "list",
            "label": "Social links",
            "itemFields": [
                {"key": "icon", "type": "text", "label": "Icon name (e.g. solar:global-bold-duotone)"},
                {"key": "label", "type": "text", "label": "Label (for accessibility)"},
                {"key": "url", "type": "text", "label": "URL"},
            ],
        },
        {"key": "contactEmail", "type": "text", "label": "Contact email"},
        {"key": "contactPhone", "type": "text", "label": "Contact phone"},
        {"key": "contactAddress", "type": "textarea", "label": "Contact address"},
        {"key": "copyrightText", "type": "text", "translatable": True, "label": "Copyright line"},
    ]
}

OLD_SCHEMA = {
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
}


def upgrade(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug="footer").update(prop_schema=NEW_SCHEMA)


def downgrade(apps, schema_editor):
    BlockType = apps.get_model("blocks", "BlockType")
    BlockType.objects.filter(slug="footer").update(prop_schema=OLD_SCHEMA)


class Migration(migrations.Migration):
    dependencies = [
        ("blocks", "0006_seed_feature_grid_callout_cards_block_types"),
    ]

    operations = [
        migrations.RunPython(upgrade, downgrade),
    ]
