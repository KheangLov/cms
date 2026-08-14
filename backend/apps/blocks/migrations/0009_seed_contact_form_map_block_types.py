from django.db import migrations

BLOCK_TYPES = [
    {
        "name": "Contact Form",
        "slug": "contact-form",
        "category": "content",
        "icon": "mdi-email-outline",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {"key": "subheading", "type": "text", "translatable": True, "label": "Subheading"},
                {"key": "submitLabel", "type": "text", "translatable": True, "label": "Submit button label"},
            ]
        },
    },
    {
        "name": "Map",
        "slug": "map",
        "category": "content",
        "icon": "mdi-map-marker-outline",
        "is_system": True,
        "prop_schema": {
            "fields": [
                {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
                {
                    "key": "embedUrl",
                    "type": "text",
                    "label": "Map embed URL (e.g. an OpenStreetMap or Google Maps embed link)",
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
        ("blocks", "0008_text_section_richtext_body"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
