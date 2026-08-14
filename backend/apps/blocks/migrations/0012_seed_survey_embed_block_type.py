from django.db import migrations

BLOCK_TYPE = {
    "name": "Survey",
    "slug": "survey-embed",
    "category": "content",
    "icon": "mdi-clipboard-list-outline",
    "is_system": True,
    "prop_schema": {
        "fields": [
            {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
            {"key": "surveyId", "type": "reference", "referenceType": "survey", "label": "Survey"},
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
        ("blocks", "0011_seed_quiz_embed_block_type"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
