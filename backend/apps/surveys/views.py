from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Survey, SurveyAnswer
from .permissions import SurveyPermission
from .serializers import SurveyPublicSerializer, SurveyResponseSerializer, SurveySerializer


def _can_manage(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.has_perm("surveys.view_survey")))


class SurveyViewSet(viewsets.ModelViewSet):
    permission_classes = [SurveyPermission]
    search_fields = ["title__en", "title__km", "slug"]

    def get_serializer_class(self):
        if self.action == "respond":
            return SurveyResponseSerializer
        return SurveySerializer if _can_manage(self.request.user) else SurveyPublicSerializer

    def get_queryset(self):
        qs = Survey.objects.prefetch_related("questions__choices")
        if not _can_manage(self.request.user):
            qs = qs.filter(is_published=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=["post"])
    def respond(self, request, pk=None):
        """Public — no login required, same as Quiz's `attempt`."""
        survey = self.get_object()
        serializer = SurveyResponseSerializer(data=request.data, context={"survey": survey, "request": request})
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(SurveyResponseSerializer(response).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def responses(self, request, pk=None):
        survey = self.get_object()
        responses = survey.responses.select_related("user").order_by("-submitted_at")
        page = self.paginate_queryset(responses)
        rows = page if page is not None else responses
        data = [
            {
                "id": r.id,
                "respondent_name": r.respondent_name,
                "respondent_email": r.respondent_email,
                "submitted_at": r.submitted_at,
                "answers": [
                    {"question_id": a.question_id, "choice_id": a.choice_id, "text": a.text}
                    for a in r.answers.all()
                ],
            }
            for r in rows
        ]
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        survey = self.get_object()
        response_count = survey.responses.count()

        questions = []
        for question in survey.questions.prefetch_related("choices").order_by("order"):
            if question.question_type == "choice":
                choices = list(question.choices.all())
                counts = {c.id: 0 for c in choices}
                for row in SurveyAnswer.objects.filter(question=question).values("choice_id").annotate(count=Count("id")):
                    if row["choice_id"] is not None:
                        counts[row["choice_id"]] = row["count"]
                total_answers = sum(counts.values())
                questions.append({
                    "id": question.id,
                    "text": question.text,
                    "question_type": "choice",
                    "choices": [
                        {
                            "id": c.id,
                            "text": c.text,
                            "count": counts.get(c.id, 0),
                            "percentage": round(counts.get(c.id, 0) / total_answers * 100, 1) if total_answers else 0,
                        }
                        for c in choices
                    ],
                })
            else:
                text_answers = list(
                    SurveyAnswer.objects.filter(question=question).exclude(text="").order_by("-id").values_list("text", flat=True)[:20]
                )
                questions.append({
                    "id": question.id,
                    "text": question.text,
                    "question_type": "text",
                    "answer_count": SurveyAnswer.objects.filter(question=question).exclude(text="").count(),
                    "recent_answers": text_answers,
                })

        return Response({"response_count": response_count, "questions": questions})
