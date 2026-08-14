from django.db.models import Avg, Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Answer, Quiz
from .permissions import QuizPermission
from .serializers import QuizAttemptSerializer, QuizPublicSerializer, QuizSerializer


def _can_manage(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.has_perm("quizzes.view_quiz")))


class QuizViewSet(viewsets.ModelViewSet):
    permission_classes = [QuizPermission]
    search_fields = ["title__en", "title__km", "slug"]

    def get_serializer_class(self):
        if self.action == "attempt":
            return QuizAttemptSerializer
        return QuizSerializer if _can_manage(self.request.user) else QuizPublicSerializer

    def get_queryset(self):
        qs = Quiz.objects.prefetch_related("questions__choices")
        if not _can_manage(self.request.user):
            qs = qs.filter(is_published=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=["post"])
    def attempt(self, request, pk=None):
        """Public — no login required to take a quiz (see Quiz model docstring).
        Scored server-side; the response includes per-question correctness so
        the taking UI can reveal right/wrong immediately."""
        quiz = self.get_object()
        serializer = QuizAttemptSerializer(data=request.data, context={"quiz": quiz, "request": request})
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()
        result = QuizAttemptSerializer(attempt, context={"quiz": quiz, "request": request})
        return Response(result.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def attempts(self, request, pk=None):
        quiz = self.get_object()
        attempts = quiz.attempts.select_related("user").order_by("-completed_at")
        page = self.paginate_queryset(attempts)
        rows = page if page is not None else attempts
        data = [
            {
                "id": a.id,
                "respondent_name": a.respondent_name,
                "respondent_email": a.respondent_email,
                "score": a.score,
                "total_questions": a.total_questions,
                "completed_at": a.completed_at,
            }
            for a in rows
        ]
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        quiz = self.get_object()
        attempts = quiz.attempts.all()
        average_score = attempts.aggregate(avg=Avg("score"))["avg"] or 0

        questions = []
        for question in quiz.questions.prefetch_related("choices").order_by("order"):
            choices = list(question.choices.all())
            counts = {c.id: 0 for c in choices}
            for row in Answer.objects.filter(question=question).values("choice_id").annotate(count=Count("id")):
                counts[row["choice_id"]] = row["count"]
            total_answers = sum(counts.values())
            correct_choice = next((c for c in choices if c.is_correct), None)
            correct_count = counts.get(correct_choice.id, 0) if correct_choice else 0
            questions.append({
                "id": question.id,
                "text": question.text,
                "choices": [
                    {
                        "id": c.id,
                        "text": c.text,
                        "is_correct": c.is_correct,
                        "count": counts.get(c.id, 0),
                        "percentage": round(counts.get(c.id, 0) / total_answers * 100, 1) if total_answers else 0,
                    }
                    for c in choices
                ],
                "correct_rate": round(correct_count / total_answers * 100, 1) if total_answers else 0,
            })

        return Response({
            "attempt_count": attempts.count(),
            "average_score": round(average_score, 1),
            "questions": questions,
        })
