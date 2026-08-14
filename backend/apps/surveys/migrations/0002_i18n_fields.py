from django.db import migrations, models


def wrap_existing_as_en(apps, schema_editor):
    Survey = apps.get_model("surveys", "Survey")
    SurveyQuestion = apps.get_model("surveys", "SurveyQuestion")
    SurveyChoice = apps.get_model("surveys", "SurveyChoice")
    for survey in Survey.objects.all():
        survey.title_i18n = {"en": survey.title} if survey.title else {}
        survey.description_i18n = {"en": survey.description} if survey.description else {}
        survey.save(update_fields=["title_i18n", "description_i18n"])
    for question in SurveyQuestion.objects.all():
        question.text_i18n = {"en": question.text} if question.text else {}
        question.save(update_fields=["text_i18n"])
    for choice in SurveyChoice.objects.all():
        choice.text_i18n = {"en": choice.text} if choice.text else {}
        choice.save(update_fields=["text_i18n"])


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        migrations.AddField("survey", "title_i18n", models.JSONField(default=dict)),
        migrations.AddField("survey", "description_i18n", models.JSONField(default=dict, blank=True)),
        migrations.AddField("surveyquestion", "text_i18n", models.JSONField(default=dict)),
        migrations.AddField("surveychoice", "text_i18n", models.JSONField(default=dict)),
        migrations.RunPython(wrap_existing_as_en, migrations.RunPython.noop),
        migrations.RemoveField("survey", "title"),
        migrations.RemoveField("survey", "description"),
        migrations.RemoveField("surveyquestion", "text"),
        migrations.RemoveField("surveychoice", "text"),
        migrations.RenameField("survey", "title_i18n", "title"),
        migrations.RenameField("survey", "description_i18n", "description"),
        migrations.RenameField("surveyquestion", "text_i18n", "text"),
        migrations.RenameField("surveychoice", "text_i18n", "text"),
    ]
