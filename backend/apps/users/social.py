from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer
from .views import set_refresh_cookie

# Same pattern as the 2FA pending-token (apps/users/two_factor.py) — a narrow,
# short-lived, single-purpose signed value, not a real JWT that would grant
# actual API access if it leaked.
_EXCHANGE_SIGNER = TimestampSigner(salt="social-login-exchange")
_EXCHANGE_MAX_AGE = 120  # 2 minutes — just long enough for the redirect round trip


class SPARedirectAccountAdapter(DefaultAccountAdapter):
    """CMS_BUILD_PROMPT.md §5.6 — "social callback → Django issues the same JWT
    pair used by normal login." allauth's own flow is session/redirect-based (a
    classic multi-page web app pattern); this bridges it to the Nuxt SPA by
    sending the browser back with a one-time exchange code instead of relying on
    the Django session cookie the SPA never otherwise uses."""

    def get_login_redirect_url(self, request):
        code = _EXCHANGE_SIGNER.sign(str(request.user.id))
        return f"{settings.FRONTEND_URL}/admin/social-callback?code={code}"


class SocialExchangeView(APIView):
    """The frontend's /admin/social-callback page calls this once with the code
    from the query string to actually get a usable JWT pair."""

    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model

        code = request.data.get("code", "")
        try:
            user_id = int(_EXCHANGE_SIGNER.unsign(code, max_age=_EXCHANGE_MAX_AGE))
        except (BadSignature, SignatureExpired, ValueError):
            return Response({"detail": "Invalid or expired code."}, status=401)

        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Invalid or expired code."}, status=401)

        from apps.activity_log.utils import log_activity

        log_activity("login", user, actor=user)

        refresh = RefreshToken.for_user(user)
        response = Response({"access": str(refresh.access_token), "user": UserSerializer(user).data})
        set_refresh_cookie(response, refresh)
        return response
