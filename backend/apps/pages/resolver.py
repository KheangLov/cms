from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blocks.serializers import PageBlockTreeSerializer
from apps.posts.models import Post
from apps.posts.serializers import PostDetailSerializer

from .models import Page
from .serializers import PageDetailSerializer


class ResolveView(APIView):
    """CMS_BUILD_PROMPT.md §5.1 — the single endpoint the Nuxt catch-all route
    (`/[...slug].vue`) uses to find out whether a URL is a Page or a Post, so
    frontend routing logic stays trivial. Public/unauthenticated — only ever
    resolves published content, same as the public list/retrieve endpoints.

    Page paths are hierarchical (walked segment by segment through `parent`),
    rooted at `/`. Post paths live under a fixed `/post/<slug>` namespace —
    "lives at its own canonical URL, independent of any Page" per §5.1 — so a
    post's URL never depends on, or collides with, the page tree. `post` is
    reserved for this: a `/post/<slug>` request never falls back to page
    lookup, even if no such post exists.

    The empty path (site root) resolves via the `homepage_page_id` Setting —
    the same "static front page" idea WordPress exposes under Settings →
    Reading. It's a plain Setting row (no new model) so the existing generic
    Settings CRUD is the entire admin UI for picking the homepage; nothing
    reserves that Page's own slug/path, so it stays reachable at its normal
    URL too, exactly like a WordPress front page.

    A materialized-path/MPTT approach would make the page walk O(1) instead of
    O(depth) — not needed at this scale yet, noted in CMS_BUILD_PROMPT.md §2.1.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        raw_path = request.query_params.get("path", "")
        path = raw_path.strip("/")
        if not path:
            return self._resolve_homepage(request)

        segments = path.split("/")

        if segments[0] == "post" and len(segments) == 2:
            post = self._resolve_post(segments[1])
            if post is not None:
                return Response(
                    {"type": "post", "data": PostDetailSerializer(post, context={"request": request}).data}
                )
            return Response({"detail": "Not found"}, status=404)

        page = self._resolve_page(segments)
        if page is not None:
            return Response(
                {"type": "page", "data": PageDetailSerializer(page, context={"request": request}).data}
            )

        return Response({"detail": "Not found"}, status=404)

    @staticmethod
    def _resolve_homepage(request):
        from apps.settings_app.models import Setting

        setting = Setting.objects.filter(key="homepage_page_id").first()
        page_id = setting.value if setting is not None else None
        if page_id is None:
            return Response({"detail": "No homepage configured"}, status=404)

        page = (
            Page.objects.filter(pk=page_id, status="published")
            .select_related("page_type", "created_by")
            .prefetch_related("translations")
            .first()
        )
        if page is None:
            return Response({"detail": "Not found"}, status=404)
        return Response({"type": "page", "data": PageDetailSerializer(page, context={"request": request}).data})

    @staticmethod
    def _resolve_post(slug):
        return (
            Post.objects.filter(slug=slug, status="published")
            .select_related("category", "author")
            .prefetch_related("translations", "tags")
            .first()
        )

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


class SiteChromeView(APIView):
    """Site-wide navbar/footer, modeled as ordinary blocks on one reserved Page
    (picked via the `site_chrome_page_id` Setting — same one-Setting-row idea as
    `homepage_page_id`). The default layout fetches this once so every public
    page gets consistent chrome without an editor re-adding it to each page.
    Public/unauthenticated, like ResolveView. Never 404s — an unconfigured or
    missing site-chrome page just means "no chrome", not an error, since the
    caller renders it unconditionally on every page load."""

    permission_classes = [AllowAny]

    def get(self, request):
        from apps.settings_app.models import Setting

        setting = Setting.objects.filter(key="site_chrome_page_id").first()
        page_id = setting.value if setting is not None else None
        if page_id is None:
            return Response({"blocks": []})

        page = Page.objects.filter(pk=page_id, status="published").first()
        if page is None:
            return Response({"blocks": []})

        top_level = page.blocks.filter(parent__isnull=True).select_related("block_type").order_by("order")
        blocks = PageBlockTreeSerializer(top_level, many=True).data
        for block in blocks:
            self._resolve_links(block.get("props") or {})
        return Response({"blocks": blocks})

    @staticmethod
    def _resolve_links(props):
        links = props.get("links")
        if not isinstance(links, list):
            return
        for link in links:
            if not isinstance(link, dict):
                continue
            page_id = link.get("pageId")
            if page_id:
                target = Page.objects.filter(pk=page_id, status="published").first()
                link["resolvedUrl"] = f"/{target.full_path()}" if target else None
            else:
                link["resolvedUrl"] = link.get("url") or "#"
