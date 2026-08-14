from django.conf import settings
from django.db import models

from apps.common.models import SoftDeleteModel, TimestampedModel


class Quiz(SoftDeleteModel):
    """A standalone, reusable entity — not page content. A page embeds a Quiz
    by id via the "quiz-embed" block, the same way it embeds a Category's posts
    via PostsBlock; the quiz itself isn't owned by any one page.

    CMS_BUILD_PROMPT.md §10.1.3 — confirmed as a dedicated app with scoring,
    attempts, and analytics, not a lightweight embedded form."""

    # {"en": "...", "km": "..."} — same per-locale-dict convention as block
    # props (ContentBlock.props), not a satellite Translation table like
    # Page/Post: each of these fields is a single piece of translatable text,
    # not a bundle of several locale-specific fields, so the lighter shape fits.
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


class Question(TimestampedModel):
    """Owned entirely by its Quiz — authored and saved as a unit (see
    QuizSerializer's replace-all-on-save), not managed as an independent
    resource, so no soft-delete/own permissions of its own."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.JSONField(default=dict)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text.get("en", "") if isinstance(self.text, dict) else str(self.text)


class Choice(TimestampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.JSONField(default=dict)
    # Never serialized to an anonymous/public client (QuizPublicSerializer omits
    # it) — a quiz taker reading the network response for their own quiz's
    # choices would trivially see the answers otherwise.
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text.get("en", "") if isinstance(self.text, dict) else str(self.text)


class QuizAttempt(TimestampedModel):
    """One complete, atomically-submitted attempt — there's no "in progress"
    state. `user` is nullable: taking a quiz never requires login (unlike
    Comments, §10.2 — a quiz is engagement/lead-gen content, not accountable
    discourse), so anonymous visitors are the expected common case."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="quiz_attempts"
    )
    respondent_name = models.CharField(max_length=200, blank=True)
    respondent_email = models.EmailField(blank=True)
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.quiz}: {self.score}/{self.total_questions}"


class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name="+")

    def __str__(self):
        return f"{self.question_id} -> {self.choice_id}"
