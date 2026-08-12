from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """One group per user (§5.15: notifications, AI job progress, media processing
    completion — all addressed to a specific user, not broadcast)."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return
        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        """Handles {"type": "notify", "payload": {...}} sent via
        apps.realtime.utils.notify_user — Channels dispatches group_send messages
        to the consumer method matching `type`."""
        await self.send_json(event["payload"])
