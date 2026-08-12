from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Media
from .permissions import MediaPermission
from .serializers import MediaSerializer
from .tasks import process_media


class MediaViewSet(viewsets.ModelViewSet):
    serializer_class = MediaSerializer
    permission_classes = [MediaPermission]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["mime_type", "processing_status", "uploaded_by"]
    search_fields = ["original_filename"]

    def get_queryset(self):
        show_trash = self.request.query_params.get("trash") == "1"
        base = Media.all_objects if show_trash else Media.objects
        qs = base.select_related("uploaded_by")
        if show_trash:
            qs = qs.filter(is_deleted=True)
        return qs

    def perform_create(self, serializer):
        file_obj = self.request.data.get("file")
        media = serializer.save(
            uploaded_by=self.request.user,
            original_filename=getattr(file_obj, "name", "") or "",
            mime_type=getattr(file_obj, "content_type", "") or "application/octet-stream",
            size_bytes=getattr(file_obj, "size", 0) or 0,
        )
        process_media.delay(media.id)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        media = Media.all_objects.get(pk=pk)
        media.restore()
        return Response(MediaSerializer(media).data)

    @action(detail=True, methods=["post"], url_path="regenerate-thumbnails")
    def regenerate_thumbnails(self, request, pk=None):
        media = self.get_object()
        media.processing_status = "pending"
        media.save(update_fields=["processing_status"])
        process_media.delay(media.id)
        return Response(MediaSerializer(media).data)
