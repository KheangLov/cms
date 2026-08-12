import base64
import io

import qrcode
from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer
from .views import set_refresh_cookie

# Deliberately separate from SimpleJWT's own tokens — a "password verified, TOTP
# still pending" state should not be usable at any other endpoint, which a real
# (if short-lived) access token would be. CMS_BUILD_PROMPT.md §5.5.
_PENDING_SIGNER = TimestampSigner(salt="2fa-pending")
_PENDING_MAX_AGE = 300  # 5 minutes to enter the code


def make_pending_token(user_id):
    return _PENDING_SIGNER.sign(str(user_id))


def _read_pending_token(token):
    try:
        return int(_PENDING_SIGNER.unsign(token, max_age=_PENDING_MAX_AGE))
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return None


class Setup2FAView(APIView):
    """Step 1 — creates (or re-creates) an *unconfirmed* TOTP device and returns a
    scannable QR code. Nothing is enabled yet; Confirm2FAView does that."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_2fa_enabled:
            return Response({"detail": "2FA is already enabled."}, status=400)
        TOTPDevice.objects.filter(user=request.user, name="default").delete()
        device = TOTPDevice.objects.create(user=request.user, name="default", confirmed=False)

        qr_image = qrcode.make(device.config_url)
        buffer = io.BytesIO()
        qr_image.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode()

        # device.key is hex (django_otp's internal storage) — authenticator apps
        # and the otpauth:// URI standard expect base32 for manual entry. The QR
        # code itself (config_url) was already correct; this text fallback for
        # "can't scan the QR" was not, and would produce codes no app agrees with.
        secret_base32 = base64.b32encode(device.bin_key).decode()

        return Response(
            {
                "secret": secret_base32,
                "otpauth_url": device.config_url,
                "qr_code": f"data:image/png;base64,{qr_b64}",
            }
        )


class Confirm2FAView(APIView):
    """Step 2 — proves the user's authenticator app is actually set up correctly
    before flipping is_2fa_enabled on. Issues one-time-use recovery codes,
    returned exactly once (nothing stores them in plaintext after this)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code", "")
        try:
            device = TOTPDevice.objects.get(user=request.user, name="default")
        except TOTPDevice.DoesNotExist:
            return Response({"detail": "Call /api/v1/auth/2fa/setup/ first."}, status=400)
        if not device.verify_token(code):
            return Response({"detail": "Invalid code."}, status=400)

        device.confirmed = True
        device.save(update_fields=["confirmed"])
        request.user.is_2fa_enabled = True
        request.user.save(update_fields=["is_2fa_enabled"])

        StaticDevice.objects.filter(user=request.user, name="recovery").delete()
        static_device = StaticDevice.objects.create(user=request.user, name="recovery")
        recovery_codes = []
        for _ in range(10):
            token = StaticToken.random_token()
            StaticToken.objects.create(device=static_device, token=token)
            recovery_codes.append(token)

        return Response({"recovery_codes": recovery_codes})


class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        TOTPDevice.objects.filter(user=request.user).delete()
        StaticDevice.objects.filter(user=request.user).delete()
        request.user.is_2fa_enabled = False
        request.user.save(update_fields=["is_2fa_enabled"])
        return Response(status=204)


class Verify2FAView(APIView):
    """Step 3 of login when 2FA is enabled — the actual code (TOTP or a recovery
    code) is checked here, and only here does a real JWT pair get issued."""

    permission_classes = [AllowAny]

    def post(self, request):
        pending_token = request.data.get("pending_token", "")
        code = request.data.get("code", "")

        user_id = _read_pending_token(pending_token)
        if user_id is None:
            return Response({"detail": "Invalid or expired pending token."}, status=401)

        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Invalid or expired pending token."}, status=401)

        device = None
        for totp_device in TOTPDevice.objects.filter(user=user, confirmed=True):
            if totp_device.verify_token(code):
                device = totp_device
                break
        if device is None:
            for static_device in StaticDevice.objects.filter(user=user):
                if static_device.verify_token(code):
                    device = static_device
                    break
        if device is None:
            return Response({"detail": "Invalid code."}, status=401)

        from apps.activity_log.utils import log_activity

        log_activity("login", user, actor=user)

        refresh = RefreshToken.for_user(user)
        response = Response({"access": str(refresh.access_token), "user": UserSerializer(user).data})
        set_refresh_cookie(response, refresh)
        return response
