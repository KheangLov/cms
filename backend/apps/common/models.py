from django.conf import settings
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Default manager — excludes soft-deleted rows. CMS_BUILD_PROMPT.md §5.9."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class SoftDeleteModel(TimestampedModel):
    """
    Shared base for user-generated content (Page, Post, Media, Comment — §4).
    Deleting sets is_deleted/deleted_at instead of removing the row; `all_objects`
    gives trash views access to soft-deleted rows the default manager hides.
    """

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
        self._log_activity("delete")

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
        self._log_activity("restore")

    def _log_activity(self, verb):
        # Local import — apps.common must not depend on apps.activity_log at
        # module-load time (activity_log's own signals fire for saves across many
        # apps and shouldn't be a hard import-time dependency of the base model
        # every content app inherits from). CMS_BUILD_PROMPT.md §5.10.
        from apps.activity_log.utils import log_activity

        log_activity(verb, self)
