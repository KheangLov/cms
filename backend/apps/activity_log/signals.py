from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .utils import log_activity

# Only these apps' models get auto-logged on save/delete — infra/audit models
# themselves (activity_log, sessions, token_blacklist, contenttypes, admin) are
# deliberately excluded. §5.10 explicit-call cases (soft delete/restore, login,
# publish) live next to their own actions instead — see apps/common/models.py,
# apps/users/views.py, apps/pages+posts/views.py.
TRACKED_APP_LABELS = {
    "pages",
    "posts",
    "media_library",
    "blocks",
    "settings_app",
    "users",
    "roles_permissions",
    "comments",
}

# Saves that only touch these fields are already logged explicitly by
# SoftDeleteModel.soft_delete()/restore() — skip to avoid a duplicate entry.
SOFT_DELETE_FIELDS = {"is_deleted", "deleted_at", "deleted_by"}


@receiver(post_save)
def log_save(sender, instance, created, update_fields, **kwargs):
    if sender._meta.app_label not in TRACKED_APP_LABELS:
        return
    if update_fields and set(update_fields) <= SOFT_DELETE_FIELDS:
        return
    log_activity("create" if created else "update", instance)


@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender._meta.app_label not in TRACKED_APP_LABELS:
        return
    log_activity("hard_delete", instance)
