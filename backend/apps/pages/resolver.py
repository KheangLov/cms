from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.models import Post
from apps.posts.serializers import PostDetailSerializer

from .models import Page
from .serializers import PageDetailSerializer


class ResolveView(APIView):
    """CMS_BUILD_PROMPT.md §5.1 — the single endpoint the Nuxt catch-all route
    (`/[...slug].vue`) uses to find out whether a URL is a Page or a Post, so
    frontend routing logic stays trivial. Public/unauthenticated — only ever
    resolves published content, same as the public list/retrieve endpoints.

    Page paths are hierarchical (walked segment by segment through `parent`);
    Post paths are flat (e.g. /blog/my-post resolves by the last segment alone).
    A materialized-path/MPTT approach would make the walk O(1) instead of O(depth)
    — not needed at this scale yet, noted in CMS_BUILD_PROMPT.md §2.1 for later.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        raw_path = request.query_params.get("path", "")
        path = raw_path.strip("/")
        if not path:
            return Response({"detail": "path query param is required"}, status=400)

        segments = path.split("/")

        page = self._resolve_page(segments)
        if page is not None:
            return Response(
                {"type": "page", "data": PageDetailSerializer(page, context={"request": request}).data}
            )

        post = (
            Post.objects.filter(slug=segments[-1], status="published")
            .select_related("category", "author")
            .prefetch_related("translations", "tags")
            .first()
        )
        if post is not None:
            return Response(
                {"type": "post", "data": PostDetailSerializer(post, context={"request": request}).data}
            )

        return Response({"detail": "Not found"}, status=404)

    @staticmethod
    def _resolve_page(segments):
        parent = None
        page = None
        for segment in segments:
            page = (
                Page.objects.filter(slug=segment, parent=parent, status="published")
                .select_related("page_type", "created_by")
                .prefetch_related("translations")
                .first()
            )
            if page is None:
                return None
            parent = page
        return page
