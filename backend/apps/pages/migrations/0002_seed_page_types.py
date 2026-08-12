from django.db import migrations

# CMS_BUILD_PROMPT.md §4 / §5.1's canonical list.
PAGE_TYPES = [
    ("Landing Page", "landing", "Marketing/landing pages built from blocks."),
    ("Blog", "blog", "Archive/index view for Post entries — see §5.1's Post-List block."),
    ("About", "about", "Static About page."),
    ("Contact", "contact", "Static Contact page, typically with a Form block."),
    ("Quiz", "quiz", "Container page for an embedded Quiz block."),
    ("Survey", "survey", "Container page for an embedded Survey block."),
    ("Custom", "custom", "Freeform page with no special behavior."),
]


def seed_page_types(apps, schema_editor):
    PageType = apps.get_model("pages", "PageType")
    for name, slug, description in PAGE_TYPES:
        PageType.objects.get_or_create(
            slug=slug, defaults={"name": name, "description": description, "is_system": True}
        )


def unseed_page_types(apps, schema_editor):
    PageType = apps.get_model("pages", "PageType")
    PageType.objects.filter(slug__in=[slug for _, slug, _ in PAGE_TYPES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_page_types, unseed_page_types),
    ]
