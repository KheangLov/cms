from rest_framework_simplejwt.authentication import JWTAuthentication

from .context import set_current_user


class TrackingJWTAuthentication(JWTAuthentication):
    """Identical to simplejwt's JWTAuthentication, except it also records the
    authenticated user in the same thread-local state CurrentRequestMiddleware
    uses — this is the actual point in the request cycle where a JWT-authenticated
    user becomes known, which is why the generic activity-log signals (§5.10) can
    rely on it for `actor` attribution."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _token = result
            set_current_user(user)
        return result
