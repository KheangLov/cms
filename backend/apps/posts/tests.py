import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .models import Post

User = get_user_model()


def _authed_client(email="admin@test.local"):
    User.objects.create_superuser(email=email, password="S3cure!2026")
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.mark.django_db
class TestPostPresentationFields:
    """Same "page settings" fields as Page — container width + background,
    independent of block content."""

    def test_defaults_to_default_width_no_background(self):
        post = Post.objects.create(slug="plain-post")

        assert post.container_width == "default"
        assert post.background_color == ""
        assert post.background_image_url == ""

    def test_can_be_set_through_the_api(self):
        client = _authed_client("post-presentation@test.local")
        post_id = client.post("/api/v1/posts/", {"slug": "styled-post"}).data["id"]

        resp = client.patch(
            f"/api/v1/posts/{post_id}/",
            {"container_width": "narrow", "background_color": "#eeeeee", "background_image_url": "/bg.jpg"},
            format="json",
        )

        assert resp.status_code == 200
        post = Post.objects.get(id=post_id)
        assert post.container_width == "narrow"
        assert post.background_color == "#eeeeee"
        assert post.background_image_url == "/bg.jpg"
