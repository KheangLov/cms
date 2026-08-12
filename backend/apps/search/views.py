from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .indexing import search_content


class SearchView(APIView):
    """CMS_BUILD_PROMPT.md §5.12 — powers both the admin "find content" search and
    an on-site search box. Public: only ever returns published content (enforced
    in search_content's ES query filter, not here)."""

    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        locale = request.query_params.get("locale", "en")
        if not query:
            return Response({"results": []})
        return Response({"results": search_content(query, locale=locale)})
