from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Comment
from .permissions import CommentPermission
from .serializers import CommentSerializer


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [CommentPermission]
    filterset_fields = ["content_type", "object_id", "status", "parent"]

    def get_queryset(self):
        qs = Comment.objects.select_related("author", "content_type")
        user = self.request.user
        can_moderate = user and user.is_authenticated and (user.is_superuser or user.has_perm("comments.moderate_comments"))
        if not can_moderate:
            if user and user.is_authenticated:
                qs = qs.filter(Q(status="approved") | Q(author=user))
            else:
                qs = qs.filter(status="approved")
        return qs

    def perform_create(self, serializer):
        from apps.realtime.utils import notify_user

        comment = serializer.save(author=self.request.user)

        target = comment.content_object
        owner_id = getattr(target, "created_by_id", None) or getattr(target, "author_id", None)
        if owner_id and owner_id != comment.author_id:
            notify_user(
                owner_id,
                {
                    "event": "comment.created",
                    "comment_id": comment.id,
                    "target_type": comment.content_type.model,
                    "target_id": comment.object_id,
                    "author": comment.author.email,
                    "body": comment.body[:140],
                },
            )

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        comment = self.get_object()
        comment.status = "approved"
        comment.save(update_fields=["status"])
        return Response(CommentSerializer(comment).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        comment = self.get_object()
        comment.status = "spam"
        comment.save(update_fields=["status"])
        return Response(CommentSerializer(comment).data)
