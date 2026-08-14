import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import ContactSubmission

User = get_user_model()


def _staff_client(email="staff@test.local"):
    User.objects.create_superuser(email=email, password="S3cure!2026")
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.mark.django_db
class TestContactSubmissions:
    """A public contact-form block posts here unauthenticated; only staff can
    read submissions back, since it's a one-way mailbox."""

    def test_anonymous_can_submit(self):
        resp = APIClient().post(
            "/api/v1/contact-submissions/",
            {"name": "Jamie Rivera", "email": "jamie@example.com", "message": "When are you open on weekends?"},
        )

        assert resp.status_code == 201
        assert ContactSubmission.objects.count() == 1
        assert ContactSubmission.objects.first().name == "Jamie Rivera"

    def test_anonymous_cannot_list_submissions(self):
        ContactSubmission.objects.create(name="A", email="a@example.com", message="hi")

        resp = APIClient().get("/api/v1/contact-submissions/")

        assert resp.status_code in (401, 403)

    def test_staff_can_list_submissions(self):
        ContactSubmission.objects.create(name="A", email="a@example.com", message="hi")
        client = _staff_client()

        resp = client.get("/api/v1/contact-submissions/")

        assert resp.status_code == 200
        assert resp.data["count"] == 1

    def test_submission_requires_valid_email(self):
        resp = APIClient().post(
            "/api/v1/contact-submissions/",
            {"name": "Jamie", "email": "not-an-email", "message": "hi"},
        )

        assert resp.status_code == 400
