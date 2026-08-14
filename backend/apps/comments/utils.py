from django.contrib.contenttypes.models import ContentType

from .models import Comment


def approved_comments_for(obj):
    """Top-level approved comments for a Page/Post instance, newest replies last.
    Shared by PageDetailSerializer/PostDetailSerializer.get_comments so the public
    resolver response carries the full thread in one request, same as `blocks`."""
    content_type = ContentType.objects.get_for_model(obj)
    return (
        Comment.objects.filter(
            content_type=content_type, object_id=obj.pk, status="approved", parent__isnull=True
        )
        .select_related("author")
        .order_by("created_at")
    )
