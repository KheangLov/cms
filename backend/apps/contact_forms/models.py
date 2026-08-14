from django.db import models

from apps.common.models import TimestampedModel


class ContactSubmission(TimestampedModel):
    """A visitor-submitted message from a public "contact-form" block.

    No email is actually sent — this dev environment has no SMTP/mail provider
    configured, so submissions are captured and reviewable in the admin instead
    of silently disappearing into an unconfigured send. `read` lets staff track
    which ones they've triaged, same idea as an inbox."""

    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
