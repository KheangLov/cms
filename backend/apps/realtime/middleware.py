from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user_from_token(token):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        validated = AccessToken(token)
        return User.objects.get(pk=validated["user_id"])
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Channels' AuthMiddlewareStack authenticates via Django sessions, which this
    app doesn't use — auth is JWT throughout (§5.4). Browsers can't attach a
    custom Authorization header to a WebSocket handshake, so the access token is
    passed as a query param instead: ws://host/ws/notifications/?token=<access>."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]
        scope["user"] = await _get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
