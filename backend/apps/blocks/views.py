from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BlockType, PageBlock, PostBlock
from .permissions import BlockPermission
from .serializers import BlockTypeSerializer, PageBlockSerializer, PostBlockSerializer


class BlockTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """The registry itself — read-only through the API; new block types are added
    by shipping a migration + a Vue component, not through end-user CRUD."""

    queryset = BlockType.objects.all()
    serializer_class = BlockTypeSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name", "slug", "category"]


class PageBlockViewSet(viewsets.ModelViewSet):
    serializer_class = PageBlockSerializer
    permission_classes = [BlockPermission]
    filterset_fields = ["page", "parent", "block_type"]

    def get_queryset(self):
        return PageBlock.objects.select_related("block_type", "parent", "page")

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        block = PageBlock.all_objects.get(pk=pk)
        block.restore()
        return Response(PageBlockSerializer(block).data)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        """Body: [{"id": 1, "order": 0, "parent": null}, ...] — one PATCH per drag
        would be chattier and racier than one atomic bulk reorder."""
        for item in request.data:
            PageBlock.objects.filter(pk=item["id"]).update(
                order=item["order"], parent_id=item.get("parent")
            )
        return Response({"status": "ok"})


class PostBlockViewSet(viewsets.ModelViewSet):
    serializer_class = PostBlockSerializer
    permission_classes = [BlockPermission]
    filterset_fields = ["post", "parent", "block_type"]

    def get_queryset(self):
        return PostBlock.objects.select_related("block_type", "parent", "post")

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        block = PostBlock.all_objects.get(pk=pk)
        block.restore()
        return Response(PostBlockSerializer(block).data)

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        for item in request.data:
            PostBlock.objects.filter(pk=item["id"]).update(
                order=item["order"], parent_id=item.get("parent")
            )
        return Response({"status": "ok"})
