from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.pages.resolver import ResolveView, SiteChromeView
from apps.search.views import SearchView
from apps.users.social import SocialExchangeView
from apps.users.urls import admin_urlpatterns as user_admin_urlpatterns

# Django's own admin site (/admin/) is deliberately not mounted — this backend is
# REST-API-only. The Nuxt admin dashboard (frontend/pages/admin/**) has full CRUD
# parity: pages, posts, media, users, roles, settings, comments, activity log.
# django.contrib.admin stays in INSTALLED_APPS (apps/*/admin.py still registers
# against it) since django-allauth soft-depends on contrib.messages being present —
# not worth the risk of touching that for a route that's already unreachable.
urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/auth/social/exchange/", SocialExchangeView.as_view(), name="social-exchange"),
    path("api/v1/", include(user_admin_urlpatterns)),
    path("api/v1/", include("apps.roles_permissions.urls")),
    path("api/v1/", include("apps.settings_app.urls")),
    path("api/v1/", include("apps.pages.urls")),
    path("api/v1/", include("apps.posts.urls")),
    path("api/v1/", include("apps.media_library.urls")),
    path("api/v1/", include("apps.blocks.urls")),
    path("api/v1/", include("apps.activity_log.urls")),
    path("api/v1/", include("apps.comments.urls")),
    path("api/v1/", include("apps.contact_forms.urls")),
    path("api/v1/", include("apps.quizzes.urls")),
    path("api/v1/", include("apps.surveys.urls")),
    path("api/v1/resolve/", ResolveView.as_view(), name="resolve"),
    path("api/v1/site-chrome/", SiteChromeView.as_view(), name="site-chrome"),
    path("api/v1/search/", SearchView.as_view(), name="search"),
    path("api/v1/", include("apps.ai_agent.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
