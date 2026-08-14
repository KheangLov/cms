from django.conf import settings
from django.db import models

from apps.common.models import SoftDeleteModel, TimestampedModel


class Survey(SoftDeleteModel):
    """Same shape as Quiz (see apps.quizzes.models.Quiz's docstring) minus
    scoring — a standalone entity a page embeds via the "survey-embed" block,
    not owned by any one page."""

    # {"en": "...", "km": "..."} — same convention as Quiz.title, see its comment.
    title = models.JSONField(default=dict)
    slug = models.SlugField(unique=True)
    description = models.JSONField(default=dict, blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title.get("en", "") if isinstance(self.title, dict) else str(self.title)


class SurveyQuestion(TimestampedModel):
    QUESTION_TYPES = [("choice", "Choice"), ("text", "Text")]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text = models.JSONField(default=dict)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default="choice")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text.get("en", "") if isinstance(self.text, dict) else str(self.text)


class SurveyChoice(TimestampedModel):
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="choices")
    text = models.JSONField(default=dict)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text.get("en", "") if isinstance(self.text, dict) else str(self.text)


class SurveyResponse(TimestampedModel):
    """One complete, atomically-submitted response — same "no in-progress
    state, no login required" shape as QuizAttempt."""

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="survey_responses"
    )
    respondent_name = models.CharField(max_length=200, blank=True)
    respondent_email = models.EmailField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.survey} response #{self.pk}"


class SurveyAnswer(models.Model):
    """`choice` is set for a `choice`-type question; `text` for a `text`-type
    one — exactly one of the two is meaningful per row, decided by the
    question it answers."""

    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name="+")
    choice = models.ForeignKey(SurveyChoice, null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    text = models.TextField(blank=True)

    def __str__(self):
        return f"{self.question_id} -> {self.choice_id or self.text[:30]}"
