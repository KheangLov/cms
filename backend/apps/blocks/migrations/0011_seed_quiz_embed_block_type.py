from django.db import migrations

BLOCK_TYPE = {
    "name": "Quiz",
    "slug": "quiz-embed",
    "category": "content",
    "icon": "mdi-clipboard-check-outline",
    "is_system": True,
    "prop_schema": {
        "fields": [
            {"key": "heading", "type": "text", "translatable": True, "label": "Heading"},
            {"key": "quizId", "type": "reference", "referenceType": "quiz", "label": "Quiz"},
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
        ("blocks", "0010_cards_image_field"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
