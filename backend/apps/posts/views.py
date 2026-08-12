from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Category, Post, Tag
from .permissions import PostPermission, TaxonomyPermission
from .serializers import CategorySerializer, PostDetailSerializer, PostSerializer, TagSerializer


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [PostPermission]
    filterset_fields = ["status", "category", "tags"]
    search_fields = ["slug", "translations__title"]
    ordering_fields = ["published_at", "created_at", "updated_at"]

    def get_serializer_class(self):
        return PostDetailSerializer if self.action == "retrieve" else PostSerializer

    def get_queryset(self):
        show_trash = self.request.query_params.get("trash") == "1"
        base = Post.all_objects if show_trash else Post.objects
        qs = base.select_related("category", "author").prefetch_related("translations", "tags")
        if show_trash:
            qs = qs.filter(is_deleted=True)
        user = self.request.user
        can_view_drafts = user and user.is_authenticated and (user.is_superuser or user.has_perm("posts.view_post"))
        if not can_view_drafts:
            qs = qs.filter(status="published")
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        from apps.activity_log.utils import log_activity

        post = self.get_object()
        post.status = "published"
        post.save(update_fields=["status"])
        log_activity("publish", post)
        return Response(PostSerializer(post).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        from apps.activity_log.utils import log_activity

        post = self.get_object()
        post.status = "draft"
        post.save(update_fields=["status"])
        log_activity("unpublish", post)
        return Response(PostSerializer(post).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        post = Post.all_objects.get(pk=pk)
        post.restore()
        return Response(PostSerializer(post).data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        post = self.get_object()
        translations = list(post.translations.all())
        tag_ids = list(post.tags.values_list("id", flat=True))
        post.pk = None
        post.slug = f"{post.slug}-copy"
        post.status = "draft"
        post.save()
        post.tags.set(tag_ids)
        for translation in translations:
            translation.pk = None
            translation.post = post
            translation.save()
        return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().prefetch_related("translations")
    serializer_class = CategorySerializer
    permission_classes = [TaxonomyPermission]
    search_fields = ["name", "slug"]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().prefetch_related("translations")
    serializer_class = TagSerializer
    permission_classes = [TaxonomyPermission]
    search_fields = ["name", "slug"]
