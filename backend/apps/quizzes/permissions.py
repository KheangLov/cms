from rest_framework import permissions


class QuizPermission(permissions.BasePermission):
    """Public read (of published quizzes only — enforced in get_queryset) and
    public quiz-taking; authoring/moderation needs the matching permission.
    Same shape as PagePermission. `attempts` (submit) is deliberately public —
    taking a quiz never requires login, see Quiz model's docstring."""

    def has_permission(self, request, view):
        action = getattr(view, "action", None)
        if action == "attempt":
            return True
        # `attempts`/`analytics` are GET requests but must NOT fall through to
        # the SAFE_METHODS-is-public rule below — they expose respondent PII
        # and (for analytics) is_correct, so this has to be checked first.
        if action in ("attempts", "analytics"):
            user = request.user
            return bool(user and user.is_authenticated and (user.is_superuser or user.has_perm("quizzes.view_quiz")))
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        if action == "destroy":
            return user.has_perm("quizzes.delete_quiz")
        if action == "create":
            return user.has_perm("quizzes.add_quiz")
        if action in ("update", "partial_update"):
            return user.has_perm("quizzes.change_quiz")
        return True
