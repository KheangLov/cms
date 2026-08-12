import threading

_local = threading.local()


def get_current_user():
    return getattr(_local, "user", None)


def get_current_ip():
    return getattr(_local, "ip", None)


def set_current_user(user):
    _local.user = user


class CurrentRequestMiddleware:
    """Stashes the request's IP in thread-local state, and the user for
    session-authenticated requests (Django admin). Also guarantees both are reset
    after the response so state never leaks into the next request served by the
    same worker thread.

    For JWT-authenticated API requests, the user is NOT available yet at this
    point — Django's middleware chain runs before DRF's own authentication step
    (which happens inside the view's dispatch()), so `request.user` here would
    just be Django's default AnonymousUser. See TrackingJWTAuthentication in
    authentication.py, which sets it once DRF actually verifies the token."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.ip = request.META.get("REMOTE_ADDR")
        _local.user = getattr(request, "user", None)
        try:
            return self.get_response(request)
        finally:
            _local.user = None
            _local.ip = None
