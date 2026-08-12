from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    """CMS_BUILD_PROMPT.md §5.10 — audit trail for mutating actions. Read-heavy,
    write-only-by-the-system (never edited by users), so no soft-delete base needed
    here — deleting audit history would defeat its purpose."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    verb = models.CharField(max_length=50)
    target_type = models.CharField(max_length=100, blank=True)  # "<app_label>.<model_name>"
    target_id = models.CharField(max_length=50, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    diff = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["target_type", "target_id"], name="activitylog_target_idx"),
            models.Index(fields=["actor", "timestamp"], name="activitylog_actor_time_idx"),
        ]

    def __str__(self):
        return f"{self.actor} {self.verb} {self.target_type}#{self.target_id}"
