from rest_framework import permissions


class SurveyPermission(permissions.BasePermission):
    """Same shape as QuizPermission. `respond` (submit) is deliberately public.
    `responses`/`analytics` are GET but must be checked *before* the
    SAFE_METHODS-is-public fallback — they expose respondent PII, and free-text
    answers specifically, so a public GET there would be a real leak (this is
    the exact ordering bug QuizPermission had before its fix)."""

    def has_permission(self, request, view):
        action = getattr(view, "action", None)
        if action == "respond":
            return True
        if action in ("responses", "analytics"):
            user = request.user
            return bool(user and user.is_authenticated and (user.is_superuser or user.has_perm("surveys.view_survey")))
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        if action == "destroy":
            return user.has_perm("surveys.delete_survey")
        if action == "create":
            return user.has_perm("surveys.add_survey")
        if action in ("update", "partial_update"):
            return user.has_perm("surveys.change_survey")
        return True
