import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import Page, PageType

User = get_user_model()


@pytest.fixture
def page_type(db):
    return PageType.objects.create(name="Test Type", slug="test-type", is_system=False)


def _authed_client(email="admin@test.local"):
    User.objects.create_superuser(email=email, password="S3cure!2026")
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.mark.django_db
class TestPagePermissions:
    """CMS_BUILD_PROMPT.md §5.4 — public read for published content, permission-
    gated writes."""

    def test_anonymous_can_read_published(self, page_type):
        Page.objects.create(slug="public-page", page_type=page_type, status="published")
        resp = APIClient().get("/api/v1/pages/")
        assert resp.status_code == 200
        assert any(p["slug"] == "public-page" for p in resp.data["results"])

    def test_anonymous_cannot_see_draft(self, page_type):
        Page.objects.create(slug="draft-page", page_type=page_type, status="draft")
        resp = APIClient().get("/api/v1/pages/")
        assert not any(p["slug"] == "draft-page" for p in resp.data["results"])

    def test_anonymous_cannot_create(self, page_type):
        resp = APIClient().post("/api/v1/pages/", {"slug": "x", "page_type": page_type.id})
        assert resp.status_code == 401

    def test_superuser_can_create(self, page_type):
        client = _authed_client()
        resp = client.post("/api/v1/pages/", {"slug": "new-page", "page_type": page_type.id})
        assert resp.status_code == 201


@pytest.mark.django_db
class TestSoftDelete:
    """CMS_BUILD_PROMPT.md §5.9 — delete sets is_deleted, doesn't remove the row;
    restore brings it back through the default manager's visibility."""

    def test_soft_delete_and_restore(self, page_type):
        client = _authed_client("admin2@test.local")
        create = client.post("/api/v1/pages/", {"slug": "deletable", "page_type": page_type.id})
        page_id = create.data["id"]

        resp = client.delete(f"/api/v1/pages/{page_id}/")
        assert resp.status_code == 204
        assert not Page.objects.filter(id=page_id).exists()
        assert Page.all_objects.filter(id=page_id).exists()

        resp = client.post(f"/api/v1/pages/{page_id}/restore/")
        assert resp.status_code == 200
        assert Page.objects.filter(id=page_id).exists()
