import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# get_asgi_application() must run before importing anything that touches models
# (Django app registry isn't ready until this call completes) — that's why the
# realtime imports are below this line, not at the top with the others.
django_asgi_app = get_asgi_application()

from apps.realtime.middleware import JWTAuthMiddleware  # noqa: E402
from apps.realtime.routing import websocket_urlpatterns  # noqa: E402

# CMS_BUILD_PROMPT.md §5.15, Phase 8 — notifications only for now (AI job
# progress, media processing, comments); presence/live-activity-feed noted as
# deferred scope, not built in this pass.
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
