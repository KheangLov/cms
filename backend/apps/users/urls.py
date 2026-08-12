from django.urls import path

from .two_factor import Confirm2FAView, Disable2FAView, Setup2FAView, Verify2FAView
from .views import LoginView, LogoutView, MeView, RefreshView, RegisterView

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
