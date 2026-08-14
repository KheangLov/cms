from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Same as DRF's stock PageNumberPagination except it actually honors
    `?page_size=` — the stock class has no page_size_query_param configured at
    all, so that override was silently ignored everywhere it was used (e.g.
    `roles/index.vue` requesting `?page_size=500` for a permissions dropdown
    that needs every permission, not just the first 20). `max_page_size` caps
    it so a client can't request an unbounded page size."""

    page_size_query_param = "page_size"
    max_page_size = 200
