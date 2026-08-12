import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

django_asgi_app = get_asgi_application()

# WebSocket routing is added per-feature as realtime lands (CMS_BUILD_PROMPT.md §5.15,
# Phase 8) — Phase 0 only needs Channels wired up and serving HTTP through the ASGI stack.
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
    }
)
