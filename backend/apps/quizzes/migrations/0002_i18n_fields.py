from django.db import migrations, models


def wrap_existing_as_en(apps, schema_editor):
    Quiz = apps.get_model("quizzes", "Quiz")
    Question = apps.get_model("quizzes", "Question")
    Choice = apps.get_model("quizzes", "Choice")
    for quiz in Quiz.objects.all():
        quiz.title_i18n = {"en": quiz.title} if quiz.title else {}
        quiz.description_i18n = {"en": quiz.description} if quiz.description else {}
        quiz.save(update_fields=["title_i18n", "description_i18n"])
    for question in Question.objects.all():
        question.text_i18n = {"en": question.text} if question.text else {}
        question.save(update_fields=["text_i18n"])
    for choice in Choice.objects.all():
        choice.text_i18n = {"en": choice.text} if choice.text else {}
        choice.save(update_fields=["text_i18n"])


class Migration(migrations.Migration):

    dependencies = [
        ("quizzes", "0001_initial"),
    ]

    operations = [
        migrations.AddField("quiz", "title_i18n", models.JSONField(default=dict)),
        migrations.AddField("quiz", "description_i18n", models.JSONField(default=dict, blank=True)),
        migrations.AddField("question", "text_i18n", models.JSONField(default=dict)),
        migrations.AddField("choice", "text_i18n", models.JSONField(default=dict)),
        migrations.RunPython(wrap_existing_as_en, migrations.RunPython.noop),
        migrations.RemoveField("quiz", "title"),
        migrations.RemoveField("quiz", "description"),
        migrations.RemoveField("question", "text"),
        migrations.RemoveField("choice", "text"),
        migrations.RenameField("quiz", "title_i18n", "title"),
        migrations.RenameField("quiz", "description_i18n", "description"),
        migrations.RenameField("question", "text_i18n", "text"),
        migrations.RenameField("choice", "text_i18n", "text"),
    ]
