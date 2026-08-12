import io

from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image

from .models import Media

# CMS_BUILD_PROMPT.md §5.3 — small/medium thumbnails + one optimized web variant,
# all WebP (real size/quality win over the original format for photos).
THUMBNAIL_SIZES = {"small": (300, 300), "medium": (800, 800)}
OPTIMIZED_QUALITY = 85
THUMBNAIL_QUALITY = 82


@shared_task
def process_media(media_id):
    """Runs off the request/response cycle — CMS_BUILD_PROMPT.md §6.1 ("never block
    the request/response cycle on slow I/O"). Non-image files (PDFs, etc.) are marked
    "skipped", not "failed" — there's nothing to thumbnail, that's not an error."""

    try:
        media = Media.objects.get(pk=media_id)
    except Media.DoesNotExist:
        return

    if not media.mime_type.startswith("image/"):
        media.processing_status = "skipped"
        media.save(update_fields=["processing_status"])
        return

    media.processing_status = "processing"
    media.save(update_fields=["processing_status"])

    try:
        media.file.open("rb")
        image = Image.open(media.file)
        image.load()
        media.width, media.height = image.size
        rgb_image = image.convert("RGB")

        for size_name, dimensions in THUMBNAIL_SIZES.items():
            thumb = rgb_image.copy()
            thumb.thumbnail(dimensions)
            buffer = io.BytesIO()
            thumb.save(buffer, format="WEBP", quality=THUMBNAIL_QUALITY)
            buffer.seek(0)
            field = getattr(media, f"thumbnail_{size_name}")
            field.save(f"{media.pk}_{size_name}.webp", ContentFile(buffer.read()), save=False)

        optimized_buffer = io.BytesIO()
        rgb_image.save(optimized_buffer, format="WEBP", quality=OPTIMIZED_QUALITY)
        optimized_buffer.seek(0)
        media.optimized.save(f"{media.pk}_optimized.webp", ContentFile(optimized_buffer.read()), save=False)

        media.processing_status = "done"
    except Exception:
        media.processing_status = "failed"
        raise
    finally:
        media.save()
        _notify_completion(media)


def _notify_completion(media):
    from apps.realtime.utils import notify_user

    notify_user(
        media.uploaded_by_id,
        {
            "event": "media.processed",
            "media_id": media.id,
            "status": media.processing_status,
            "original_filename": media.original_filename,
        },
    )
