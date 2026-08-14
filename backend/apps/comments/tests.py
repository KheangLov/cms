import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from apps.posts.models import Post

from .models import Comment

User = get_user_model()


@pytest.fixture
def post(db):
    return Post.objects.create(slug="threaded-post", status="published")


@pytest.fixture
def commenter(db):
    return User.objects.create_user(email="commenter@test.local", password="S3cure!2026", first_name="Jamie")


@pytest.mark.django_db
class TestCommentsInDetailResponse:
    """The public site has no authenticated /api/v1/comments/ access, so
    PostDetailSerializer/PageDetailSerializer must carry the thread themselves —
    same pattern as `blocks`."""

    def test_approved_top_level_comment_appears(self, post, commenter):
        Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id,
            author=commenter,
            body="Great read!",
            status="approved",
        )

        resp = APIClient().get(f"/api/v1/posts/{post.id}/")

        assert resp.status_code == 200
        assert len(resp.data["comments"]) == 1
        assert resp.data["comments"][0]["body"] == "Great read!"
        assert resp.data["comments"][0]["author_name"] == "Jamie"

    def test_pending_comment_is_hidden(self, post, commenter):
        Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id,
            author=commenter,
            body="Awaiting moderation",
            status="pending",
        )

        resp = APIClient().get(f"/api/v1/posts/{post.id}/")

        assert resp.data["comments"] == []

    def test_replies_are_nested_under_their_parent(self, post, commenter):
        root = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id,
            author=commenter,
            body="Root comment",
            status="approved",
        )
        Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id,
            author=commenter,
            parent=root,
            body="A reply",
            status="approved",
        )

        resp = APIClient().get(f"/api/v1/posts/{post.id}/")

        assert len(resp.data["comments"]) == 1
        assert len(resp.data["comments"][0]["replies"]) == 1
        assert resp.data["comments"][0]["replies"][0]["body"] == "A reply"

    def test_comments_disabled_hides_existing_comments(self, post, commenter):
        Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.id,
            author=commenter,
            body="Should be hidden",
            status="approved",
        )
        post.comments_enabled = False
        post.save(update_fields=["comments_enabled"])

        resp = APIClient().get(f"/api/v1/posts/{post.id}/")

        assert resp.data["comments"] == []
