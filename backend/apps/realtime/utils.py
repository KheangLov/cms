from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def notify_user(user_id, payload):
    """Fire-and-forget push to one user's notification group. Safe to call from
    sync code (views, Celery tasks) — wraps the async channel layer call."""
    if not user_id:
        return
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "notify", "payload": payload},
    )
