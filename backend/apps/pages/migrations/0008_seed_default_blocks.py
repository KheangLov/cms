from django.db import migrations


def t(value):
    return {"en": value}


# One sensible starting point per page type — generic placeholder copy an
# editor is expected to replace, not finished content. `quiz`/`survey` stay
# minimal since no quiz/survey embed block type exists yet; `custom` stays
# empty on purpose (freeform is the point of that type).
DEFAULT_BLOCKS = {
    "landing": [
        {
            "block_type": "hero",
            "props": {
                "heading": t("Welcome"),
                "subheading": t("Tell visitors what this page is about."),
                "ctaLabel": t("Learn More"),
                "ctaUrl": "#",
            },
        },
        {
            "block_type": "text-section",
            "props": {"heading": t("About This Page"), "body": t("Replace this placeholder text with your own content.")},
        },
    ],
    "about": [
        {"block_type": "hero", "props": {"heading": t("About Us"), "subheading": t("Tell your story.")}},
        {"block_type": "text-section", "props": {"heading": t("Our Mission"), "body": t("Describe your mission here.")}},
        {"block_type": "text-section", "props": {"heading": t("Our Story"), "body": t("Share your story here.")}},
    ],
    "contact": [
        {"block_type": "hero", "props": {"heading": t("Contact Us"), "subheading": t("We'd love to hear from you.")}},
        {
            "block_type": "columns",
            "props": {"columnCount": 2},
            "children": [
                {"block_type": "text-section", "props": {"heading": t("Get in Touch"), "body": t("Add your contact details here.")}},
                {"block_type": "text-section", "props": {"heading": t("Visit Us"), "body": t("Add your address here.")}},
            ],
        },
        {
            "block_type": "contact-form",
            "props": {"heading": t("Send Us a Message"), "subheading": t(""), "submitLabel": t("Send Message")},
        },
    ],
    "blog": [
        {"block_type": "hero", "props": {"heading": t("Blog"), "subheading": t("Latest updates and articles.")}},
        {"block_type": "posts", "props": {"heading": t("Latest Posts"), "categorySlug": "", "count": 6}},
    ],
    "quiz": [
        {"block_type": "hero", "props": {"heading": t("Quiz"), "subheading": t("Test your knowledge.")}},
    ],
    "survey": [
        {"block_type": "hero", "props": {"heading": t("Survey"), "subheading": t("We value your feedback.")}},
    ],
    "custom": [],
}


def seed(apps, schema_editor):
    PageType = apps.get_model("pages", "PageType")
    for slug, blocks in DEFAULT_BLOCKS.items():
        PageType.objects.filter(slug=slug).update(default_blocks=blocks)


def unseed(apps, schema_editor):
    PageType = apps.get_model("pages", "PageType")
    PageType.objects.filter(slug__in=DEFAULT_BLOCKS.keys()).update(default_blocks=[])


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0007_pagetype_default_blocks"),
        ("blocks", "0010_cards_image_field"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
