import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from .models import Answer, Choice, Question, Quiz, QuizAttempt

User = get_user_model()


def _authed_client(email="admin@test.local"):
    User.objects.create_superuser(email=email, password="S3cure!2026")
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


def _staff_client(email, perm_codenames):
    user = User.objects.create_user(email=email, password="S3cure!2026", is_staff=True)
    for codename in perm_codenames:
        user.user_permissions.add(Permission.objects.get(codename=codename, content_type__app_label="quizzes"))
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.fixture
def published_quiz(db):
    quiz = Quiz.objects.create(
        title={"en": "Sample Quiz", "km": "កម្រងសំណួរគំរូ"}, slug="sample-quiz", is_published=True
    )
    q1 = Question.objects.create(quiz=quiz, text={"en": "2 + 2?", "km": "២ + ២?"}, order=0)
    Choice.objects.create(question=q1, text={"en": "3", "km": "៣"}, is_correct=False, order=0)
    Choice.objects.create(question=q1, text={"en": "4", "km": "៤"}, is_correct=True, order=1)
    q2 = Question.objects.create(quiz=quiz, text={"en": "Capital of France?", "km": "រាជធានីបារាំង?"}, order=1)
    Choice.objects.create(question=q2, text={"en": "Paris", "km": "ប៉ារីស"}, is_correct=True, order=0)
    Choice.objects.create(question=q2, text={"en": "Lyon", "km": "លីយុង"}, is_correct=False, order=1)
    return quiz


@pytest.mark.django_db
class TestQuizVisibility:
    def test_anonymous_can_read_published_quiz(self, published_quiz):
        resp = APIClient().get(f"/api/v1/quizzes/{published_quiz.id}/")
        assert resp.status_code == 200
        assert resp.data["title"] == {"en": "Sample Quiz", "km": "កម្រងសំណួរគំរូ"}

    def test_anonymous_cannot_see_draft_quiz(self):
        quiz = Quiz.objects.create(title="Draft", slug="draft-quiz", is_published=False)
        resp = APIClient().get(f"/api/v1/quizzes/{quiz.id}/")
        assert resp.status_code == 404

    def test_public_serializer_never_exposes_is_correct(self, published_quiz):
        resp = APIClient().get(f"/api/v1/quizzes/{published_quiz.id}/")
        for question in resp.data["questions"]:
            for choice in question["choices"]:
                assert "is_correct" not in choice

    def test_anonymous_cannot_create_quiz(self):
        resp = APIClient().post("/api/v1/quizzes/", {"title": "x", "slug": "x"})
        assert resp.status_code == 401


@pytest.mark.django_db
class TestQuizAuthoring:
    def test_superuser_can_create_quiz_with_nested_questions(self):
        client = _authed_client()
        resp = client.post(
            "/api/v1/quizzes/",
            {
                "title": {"en": "New Quiz", "km": "កម្រងសំណួរថ្មី"},
                "slug": "new-quiz",
                "questions": [
                    {
                        "text": {"en": "Q1", "km": "សំណួរទី១"},
                        "choices": [
                            {"text": {"en": "A", "km": "ក"}, "is_correct": True},
                            {"text": {"en": "B", "km": "ខ"}, "is_correct": False},
                        ],
                    },
                ],
            },
            format="json",
        )
        assert resp.status_code == 201
        quiz = Quiz.objects.get(id=resp.data["id"])
        assert quiz.title == {"en": "New Quiz", "km": "កម្រងសំណួរថ្មី"}
        assert quiz.questions.count() == 1
        assert quiz.questions.first().choices.count() == 2

    def test_update_replaces_questions_wholesale(self, published_quiz):
        client = _authed_client("editor1@test.local")
        old_question_ids = list(published_quiz.questions.values_list("id", flat=True))

        resp = client.patch(
            f"/api/v1/quizzes/{published_quiz.id}/",
            {"questions": [{"text": "Only question now", "choices": [{"text": "Yes", "is_correct": True}]}]},
            format="json",
        )

        assert resp.status_code == 200
        published_quiz.refresh_from_db()
        assert published_quiz.questions.count() == 1
        assert not Question.objects.filter(id__in=old_question_ids).exists()

    def test_staff_without_permission_cannot_create(self):
        User.objects.create_user(email="noperm@test.local", password="S3cure!2026", is_staff=True)
        client = APIClient()
        login = client.post("/api/v1/auth/login/", {"email": "noperm@test.local", "password": "S3cure!2026"})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        resp = client.post("/api/v1/quizzes/", {"title": "x", "slug": "x2"})
        assert resp.status_code == 403


@pytest.mark.django_db
class TestQuizAttempts:
    def test_anonymous_can_submit_attempt_no_login_required(self, published_quiz):
        q1, q2 = published_quiz.questions.order_by("order")
        correct_choice_q1 = q1.choices.get(is_correct=True)
        correct_choice_q2 = q2.choices.get(is_correct=True)

        resp = APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {"answers": [{"question_id": q1.id, "choice_id": correct_choice_q1.id}, {"question_id": q2.id, "choice_id": correct_choice_q2.id}]},
            format="json",
        )

        assert resp.status_code == 201
        assert resp.data["score"] == 2
        assert resp.data["total_questions"] == 2
        assert all(pq["correct"] for pq in resp.data["per_question"])

    def test_scoring_ignores_client_submitted_score(self, published_quiz):
        q1, q2 = published_quiz.questions.order_by("order")
        wrong_choice_q1 = q1.choices.get(is_correct=False)
        wrong_choice_q2 = q2.choices.get(is_correct=False)

        resp = APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {
                "score": 999,  # attacker-supplied, must be ignored
                "answers": [{"question_id": q1.id, "choice_id": wrong_choice_q1.id}, {"question_id": q2.id, "choice_id": wrong_choice_q2.id}],
            },
            format="json",
        )

        assert resp.status_code == 201
        assert resp.data["score"] == 0

    def test_unknown_question_and_choice_ids_are_skipped_not_fatal(self, published_quiz):
        resp = APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {"answers": [{"question_id": 999999, "choice_id": 999999}]},
            format="json",
        )

        assert resp.status_code == 201
        assert resp.data["score"] == 0
        assert QuizAttempt.objects.get(id=resp.data["id"]).answers.count() == 0

    def test_attempt_creates_answer_rows(self, published_quiz):
        q1 = published_quiz.questions.order_by("order").first()
        choice = q1.choices.first()

        resp = APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {"answers": [{"question_id": q1.id, "choice_id": choice.id}]},
            format="json",
        )

        attempt = QuizAttempt.objects.get(id=resp.data["id"])
        assert Answer.objects.filter(attempt=attempt).count() == 1
        assert attempt.user is None

    def test_anonymous_cannot_list_attempts(self, published_quiz):
        resp = APIClient().get(f"/api/v1/quizzes/{published_quiz.id}/attempts/")
        assert resp.status_code in (401, 403)

    def test_staff_with_view_permission_can_list_attempts(self, published_quiz):
        q1 = published_quiz.questions.order_by("order").first()
        APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {"answers": [{"question_id": q1.id, "choice_id": q1.choices.first().id}]},
            format="json",
        )
        client = _staff_client("viewer@test.local", ["view_quiz"])

        resp = client.get(f"/api/v1/quizzes/{published_quiz.id}/attempts/")

        assert resp.status_code == 200
        assert resp.data["count"] == 1


@pytest.mark.django_db
class TestQuizAnalytics:
    def test_analytics_reports_attempt_count_and_average_score(self, published_quiz):
        q1, q2 = published_quiz.questions.order_by("order")
        correct_q1 = q1.choices.get(is_correct=True)
        wrong_q1 = q1.choices.get(is_correct=False)
        correct_q2 = q2.choices.get(is_correct=True)

        APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {"answers": [{"question_id": q1.id, "choice_id": correct_q1.id}, {"question_id": q2.id, "choice_id": correct_q2.id}]},
            format="json",
        )
        APIClient().post(
            f"/api/v1/quizzes/{published_quiz.id}/attempt/",
            {"answers": [{"question_id": q1.id, "choice_id": wrong_q1.id}]},
            format="json",
        )

        client = _staff_client("analyst@test.local", ["view_quiz"])
        resp = client.get(f"/api/v1/quizzes/{published_quiz.id}/analytics/")

        assert resp.status_code == 200
        assert resp.data["attempt_count"] == 2
        q1_data = next(q for q in resp.data["questions"] if q["id"] == q1.id)
        assert q1_data["correct_rate"] == 50.0

    def test_anonymous_cannot_view_analytics(self, published_quiz):
        resp = APIClient().get(f"/api/v1/quizzes/{published_quiz.id}/analytics/")
        assert resp.status_code in (401, 403)
