import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from .models import Survey, SurveyAnswer, SurveyChoice, SurveyQuestion, SurveyResponse

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
        user.user_permissions.add(Permission.objects.get(codename=codename, content_type__app_label="surveys"))
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.fixture
def published_survey(db):
    survey = Survey.objects.create(
        title={"en": "Sample Survey", "km": "ការស្ទង់មតិគំរូ"}, slug="sample-survey", is_published=True
    )
    q1 = SurveyQuestion.objects.create(
        survey=survey, text={"en": "How was your visit?", "km": "តើការមកលេងរបស់អ្នកយ៉ាងណាដែរ?"}, question_type="choice", order=0
    )
    SurveyChoice.objects.create(question=q1, text={"en": "Great", "km": "ល្អណាស់"}, order=0)
    SurveyChoice.objects.create(question=q1, text={"en": "Okay", "km": "មធ្យម"}, order=1)
    q2 = SurveyQuestion.objects.create(
        survey=survey, text={"en": "Any other feedback?", "km": "មតិផ្សេងទៀត?"}, question_type="text", order=1
    )
    return survey


@pytest.mark.django_db
class TestSurveyVisibility:
    def test_anonymous_can_read_published_survey(self, published_survey):
        resp = APIClient().get(f"/api/v1/surveys/{published_survey.id}/")
        assert resp.status_code == 200
        assert resp.data["title"] == {"en": "Sample Survey", "km": "ការស្ទង់មតិគំរូ"}

    def test_anonymous_cannot_see_draft_survey(self):
        survey = Survey.objects.create(title="Draft", slug="draft-survey", is_published=False)
        resp = APIClient().get(f"/api/v1/surveys/{survey.id}/")
        assert resp.status_code == 404

    def test_anonymous_cannot_create_survey(self):
        resp = APIClient().post("/api/v1/surveys/", {"title": "x", "slug": "x"})
        assert resp.status_code == 401


@pytest.mark.django_db
class TestSurveyAuthoring:
    def test_superuser_can_create_survey_with_mixed_question_types(self):
        client = _authed_client()
        resp = client.post(
            "/api/v1/surveys/",
            {
                "title": {"en": "New Survey", "km": "ការស្ទង់មតិថ្មី"},
                "slug": "new-survey",
                "questions": [
                    {
                        "text": {"en": "Choice Q", "km": "សំណួរជម្រើស"},
                        "question_type": "choice",
                        "choices": [{"text": {"en": "A", "km": "ក"}}, {"text": {"en": "B", "km": "ខ"}}],
                    },
                    {"text": {"en": "Text Q", "km": "សំណួរអត្ថបទ"}, "question_type": "text"},
                ],
            },
            format="json",
        )
        assert resp.status_code == 201
        survey = Survey.objects.get(id=resp.data["id"])
        assert survey.title == {"en": "New Survey", "km": "ការស្ទង់មតិថ្មី"}
        assert survey.questions.count() == 2
        assert survey.questions.get(question_type="choice").choices.count() == 2

    def test_update_replaces_questions_wholesale(self, published_survey):
        client = _authed_client("editor1@test.local")
        old_ids = list(published_survey.questions.values_list("id", flat=True))

        resp = client.patch(
            f"/api/v1/surveys/{published_survey.id}/",
            {"questions": [{"text": "Only question now", "question_type": "text"}]},
            format="json",
        )

        assert resp.status_code == 200
        published_survey.refresh_from_db()
        assert published_survey.questions.count() == 1
        assert not SurveyQuestion.objects.filter(id__in=old_ids).exists()


@pytest.mark.django_db
class TestSurveyResponses:
    def test_anonymous_can_submit_response_no_login_required(self, published_survey):
        q1, q2 = published_survey.questions.order_by("order")
        choice = q1.choices.first()

        resp = APIClient().post(
            f"/api/v1/surveys/{published_survey.id}/respond/",
            {"answers": [{"question_id": q1.id, "choice_id": choice.id}, {"question_id": q2.id, "text": "Loved the staff."}]},
            format="json",
        )

        assert resp.status_code == 201
        response = SurveyResponse.objects.get(id=resp.data["id"])
        assert response.answers.count() == 2
        assert response.user is None

    def test_choice_answer_with_unknown_choice_id_is_skipped(self, published_survey):
        q1 = published_survey.questions.get(question_type="choice")

        resp = APIClient().post(
            f"/api/v1/surveys/{published_survey.id}/respond/",
            {"answers": [{"question_id": q1.id, "choice_id": 999999}]},
            format="json",
        )

        assert resp.status_code == 201
        assert SurveyResponse.objects.get(id=resp.data["id"]).answers.count() == 0

    def test_blank_text_answer_is_skipped(self, published_survey):
        q2 = published_survey.questions.get(question_type="text")

        resp = APIClient().post(
            f"/api/v1/surveys/{published_survey.id}/respond/",
            {"answers": [{"question_id": q2.id, "text": "   "}]},
            format="json",
        )

        assert resp.status_code == 201
        assert SurveyResponse.objects.get(id=resp.data["id"]).answers.count() == 0

    def test_anonymous_cannot_list_responses(self, published_survey):
        resp = APIClient().get(f"/api/v1/surveys/{published_survey.id}/responses/")
        assert resp.status_code in (401, 403)

    def test_staff_with_permission_can_list_responses(self, published_survey):
        q1 = published_survey.questions.get(question_type="choice")
        APIClient().post(
            f"/api/v1/surveys/{published_survey.id}/respond/",
            {"answers": [{"question_id": q1.id, "choice_id": q1.choices.first().id}]},
            format="json",
        )
        client = _staff_client("viewer@test.local", ["view_survey"])

        resp = client.get(f"/api/v1/surveys/{published_survey.id}/responses/")

        assert resp.status_code == 200
        assert resp.data["count"] == 1


@pytest.mark.django_db
class TestSurveyAnalytics:
    def test_analytics_breaks_down_choice_and_text_questions_separately(self, published_survey):
        q1, q2 = published_survey.questions.order_by("order")
        choice = q1.choices.first()

        APIClient().post(
            f"/api/v1/surveys/{published_survey.id}/respond/",
            {"answers": [{"question_id": q1.id, "choice_id": choice.id}, {"question_id": q2.id, "text": "Great service."}]},
            format="json",
        )

        client = _staff_client("analyst@test.local", ["view_survey"])
        resp = client.get(f"/api/v1/surveys/{published_survey.id}/analytics/")

        assert resp.status_code == 200
        assert resp.data["response_count"] == 1
        choice_q = next(q for q in resp.data["questions"] if q["question_type"] == "choice")
        text_q = next(q for q in resp.data["questions"] if q["question_type"] == "text")
        assert choice_q["choices"][0]["count"] == 1
        assert text_q["recent_answers"] == ["Great service."]

    def test_anonymous_cannot_view_analytics(self, published_survey):
        resp = APIClient().get(f"/api/v1/surveys/{published_survey.id}/analytics/")
        assert resp.status_code in (401, 403)
