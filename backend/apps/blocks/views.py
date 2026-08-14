import django_filters
from django.db import transaction
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BlockType, PageBlock, PostBlock
from .permissions import BlockPermission
from .serializers import BlockTypeSerializer, PageBlockSerializer, PostBlockSerializer


def _apply_reorder(model, owner_field, payload):
    """Validate and apply a bulk block reorder.

    Returns (response_body, status). Previously this walked the raw request body
    and called .update() per item, which meant:
      * a malformed body (dict instead of list, missing "id", non-int "order")
        raised straight out of the view as a 500;
      * unknown ids silently no-opped but still returned {"status": "ok"};
      * nothing scoped the update to one parent, so a caller could reorder — and
        reparent — blocks belonging to a page/post they never named;
      * despite the docstring promising one atomic reorder, each row was its own
        statement, so a partial failure left the ordering half-applied.
    """
    if not isinstance(payload, list):
        return {"detail": "Expected a list of {id, order, parent} objects."}, 400

    cleaned = []
    for entry in payload:
        if not isinstance(entry, dict):
            return {"detail": "Each item must be an object."}, 400
        try:
            block_id = int(entry["id"])
            order = int(entry["order"])
        except (KeyError, TypeError, ValueError):
            return {"detail": "Each item needs an integer 'id' and 'order'."}, 400
        parent = entry.get("parent")
        if parent is not None:
            try:
                parent = int(parent)
            except (TypeError, ValueError):
                return {"detail": "'parent' must be an integer or null."}, 400
        cleaned.append((block_id, order, parent))

    if not cleaned:
        return {"status": "ok", "updated": 0}, 200

    ids = [c[0] for c in cleaned]
    blocks = {b.pk: b for b in model.objects.filter(pk__in=ids)}
    missing = [i for i in ids if i not in blocks]
    if missing:
        return {"detail": f"Unknown block ids: {sorted(missing)}"}, 400

    # Every block in one reorder must belong to the same page/post — otherwise a
    # single call could shuffle content across objects.
    owners = {getattr(b, f"{owner_field}_id") for b in blocks.values()}
    if len(owners) > 1:
        return {"detail": f"All blocks must belong to the same {owner_field}."}, 400
    owner_id = owners.pop()

    parent_ids = {c[2] for c in cleaned if c[2] is not None}
    if parent_ids:
        valid_parents = set(
            model.objects.filter(pk__in=parent_ids, **{f"{owner_field}_id": owner_id})
            .values_list("pk", flat=True)
        )
        bad = parent_ids - valid_parents
        if bad:
            return {"detail": f"Parent blocks not on this {owner_field}: {sorted(bad)}"}, 400
        if parent_ids & set(ids) and any(c[0] == c[2] for c in cleaned):
            return {"detail": "A block cannot be its own parent."}, 400

    with transaction.atomic():
        for block_id, order, parent in cleaned:
            model.objects.filter(pk=block_id).update(order=order, parent_id=parent)

    return {"status": "ok", "updated": len(cleaned)}, 200


class BlockTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """The registry itself — read-only through the API; new block types are added
    by shipping a migration + a Vue component, not through end-user CRUD."""

    queryset = BlockType.objects.all()
    serializer_class = BlockTypeSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name", "slug", "category"]


class PageBlockFilter(django_filters.FilterSet):
    """`?page=` is claimed by DRF's PageNumberPagination, so declaring "page" as a
    filterset field made it unreachable — `?page=3` was read as "results page 3"
    and returned {"detail": "Invalid page."} (404) instead of filtering. Renaming
    the paginator's query param would break every existing paginated caller, so
    the FK filter is exposed under the non-colliding `page_id` instead.
    """

    page_id = django_filters.NumberFilter(field_name="page_id")

    class Meta:
        model = PageBlock
        fields = ["parent", "block_type"]


class PageBlockViewSet(viewsets.ModelViewSet):
    serializer_class = PageBlockSerializer
    permission_classes = [BlockPermission]
    filterset_class = PageBlockFilter

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
        body, status = _apply_reorder(PageBlock, "page", request.data)
        return Response(body, status=status)


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
        body, status = _apply_reorder(PostBlock, "post", request.data)
        return Response(body, status=status)
