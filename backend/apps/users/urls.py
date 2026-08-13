from django.urls import path
from rest_framework.routers import DefaultRouter

from .two_factor import Confirm2FAView, Disable2FAView, Setup2FAView, Verify2FAView
from .views import LoginView, LogoutView, MeView, RefreshView, RegisterView, UserViewSet

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("2fa/setup/", Setup2FAView.as_view(), name="2fa-setup"),
    path("2fa/confirm/", Confirm2FAView.as_view(), name="2fa-confirm"),
    path("2fa/disable/", Disable2FAView.as_view(), name="2fa-disable"),
    path("2fa/verify/", Verify2FAView.as_view(), name="2fa-verify"),
]

# Separate from the /auth/ self-service paths above — registered at /api/v1/ directly
# (not /api/v1/auth/), see config/urls.py. Kept in this app rather than a new one since
# UserViewSet is just administration over the same User model, not a new domain.
admin_router = DefaultRouter()
admin_router.register("users", UserViewSet, basename="user")
admin_urlpatterns = admin_router.urls
