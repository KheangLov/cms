from .context import get_current_ip, get_current_user


def log_activity(verb, instance, diff=None, actor=None):
    """`actor` defaults to the current request's user (thread-local). Pass it
    explicitly for events where that's wrong or unavailable — e.g. login: the
    request that logs someone in is still anonymous when the middleware captures
    it, since the JWT doesn't exist yet at that point in the request."""
    from .models import ActivityLog

    if actor is None:
        actor = get_current_user()
    ActivityLog.objects.create(
        actor=actor if actor and getattr(actor, "is_authenticated", False) else None,
        verb=verb,
        target_type=f"{instance._meta.app_label}.{instance._meta.model_name}",
        target_id=str(instance.pk),
        target_repr=str(instance)[:255],
        diff=diff or {},
        ip_address=get_current_ip(),
    )
