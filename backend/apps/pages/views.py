from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Page, PageType
from .permissions import PagePermission
from .serializers import PageDetailSerializer, PageSerializer, PageTypeSerializer


class PageViewSet(viewsets.ModelViewSet):
    """Baseline CRUD contract from CMS_BUILD_PROMPT.md §5.16 (pagination, filter,
    search, ordering, soft-delete, restore) plus the extra actions §5.1 calls for:
    publish, unpublish, duplicate, restore. `preview` is just GET on an unpublished
    page's detail endpoint for a user with view_page — no separate action needed."""

    permission_classes = [PagePermission]
    filterset_fields = ["page_type", "status", "parent"]
    search_fields = ["slug", "translations__title"]
    ordering_fields = ["created_at", "updated_at", "publish_at", "slug"]

    def get_serializer_class(self):
        return PageDetailSerializer if self.action == "retrieve" else PageSerializer

    def get_queryset(self):
        show_trash = self.request.query_params.get("trash") == "1"
        base = Page.all_objects if show_trash else Page.objects
        qs = base.select_related("page_type", "created_by", "parent").prefetch_related("translations")
        if show_trash:
            qs = qs.filter(is_deleted=True)
        user = self.request.user
        can_view_drafts = user and user.is_authenticated and (user.is_superuser or user.has_perm("pages.view_page"))
        if not can_view_drafts:
            qs = qs.filter(status="published")
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        from apps.activity_log.utils import log_activity

        page = self.get_object()
        page.status = "published"
        page.save(update_fields=["status"])
        log_activity("publish", page)
        return Response(PageSerializer(page).data)

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        from apps.activity_log.utils import log_activity

        page = self.get_object()
        page.status = "draft"
        page.save(update_fields=["status"])
        log_activity("unpublish", page)
        return Response(PageSerializer(page).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        page = Page.all_objects.get(pk=pk)
        page.restore()
        return Response(PageSerializer(page).data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        page = self.get_object()
        translations = list(page.translations.all())
        page.pk = None
        page.slug = f"{page.slug}-copy"
        page.status = "draft"
        page.save()
        for translation in translations:
            translation.pk = None
            translation.page = page
            translation.save()
        return Response(PageSerializer(page).data, status=status.HTTP_201_CREATED)


class PageTypeViewSet(viewsets.ModelViewSet):
    queryset = PageType.objects.all()
    serializer_class = PageTypeSerializer
    permission_classes = [PagePermission]
    search_fields = ["name", "slug"]
