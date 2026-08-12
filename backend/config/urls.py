from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.pages.resolver import ResolveView
from apps.search.views import SearchView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/", include("apps.roles_permissions.urls")),
    path("api/v1/", include("apps.settings_app.urls")),
    path("api/v1/", include("apps.pages.urls")),
    path("api/v1/", include("apps.posts.urls")),
    path("api/v1/", include("apps.media_library.urls")),
    path("api/v1/", include("apps.blocks.urls")),
    path("api/v1/", include("apps.activity_log.urls")),
    path("api/v1/", include("apps.comments.urls")),
    path("api/v1/resolve/", ResolveView.as_view(), name="resolve"),
    path("api/v1/search/", SearchView.as_view(), name="search"),
    path("api/v1/", include("apps.ai_agent.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
