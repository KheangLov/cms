from django.conf import settings
from elasticsearch import Elasticsearch, NotFoundError

# CMS_BUILD_PROMPT.md §5.12 — full-text search across pages/posts, both locales.
# One index, documents keyed "<type>-<id>-<locale>" so each locale is independently
# searchable/removable without touching the others.
INDEX_NAME = "cms_content"
LOCALES = ("en", "km")


def get_client():
    return Elasticsearch(settings.ELASTICSEARCH_URL)


def ensure_index():
    client = get_client()
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "type": {"type": "keyword"},
                    "object_id": {"type": "integer"},
                    "locale": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "url_path": {"type": "keyword"},
                }
            },
        )


def _extract_block_text(blocks, locale):
    """Block props are a flexible JSON blob (§4) — pull every string/translatable
    value out of it recursively so search covers actual page-builder content, not
    just the page's own title/meta fields."""
    texts = []
    for block in blocks:
        for value in (block.props or {}).values():
            if isinstance(value, dict):
                texts.append(str(value.get(locale) or value.get("en") or ""))
            elif isinstance(value, str):
                texts.append(value)
        texts.append(_extract_block_text(block.children.all(), locale))
    return " ".join(t for t in texts if t)


def _delete_doc(doc_id):
    client = get_client()
    try:
        client.delete(index=INDEX_NAME, id=doc_id)
    except NotFoundError:
        pass


def index_page(page):
    ensure_index()
    client = get_client()
    if page.is_deleted or page.status != "published":
        for locale in LOCALES:
            _delete_doc(f"page-{page.id}-{locale}")
        return
    top_blocks = page.blocks.filter(parent__isnull=True)
    for translation in page.translations.all():
        content = _extract_block_text(top_blocks, translation.locale)
        client.index(
            index=INDEX_NAME,
            id=f"page-{page.id}-{translation.locale}",
            document={
                "type": "page",
                "object_id": page.id,
                "locale": translation.locale,
                "status": page.status,
                "title": translation.title,
                "content": content,
                "url_path": page.full_path(),
            },
        )


def index_post(post):
    ensure_index()
    client = get_client()
    if post.is_deleted or post.status != "published":
        for locale in LOCALES:
            _delete_doc(f"post-{post.id}-{locale}")
        return
    top_blocks = post.blocks.filter(parent__isnull=True)
    for translation in post.translations.all():
        content = _extract_block_text(top_blocks, translation.locale)
        client.index(
            index=INDEX_NAME,
            id=f"post-{post.id}-{translation.locale}",
            document={
                "type": "post",
                "object_id": post.id,
                "locale": translation.locale,
                "status": post.status,
                "title": translation.title,
                "content": f"{translation.excerpt} {content}",
                "url_path": post.slug,
            },
        )


def remove_page(page_id):
    for locale in LOCALES:
        _delete_doc(f"page-{page_id}-{locale}")


def remove_post(post_id):
    for locale in LOCALES:
        _delete_doc(f"post-{post_id}-{locale}")


def search_content(query, locale="en"):
    ensure_index()
    client = get_client()
    resp = client.search(
        index=INDEX_NAME,
        query={
            "bool": {
                "must": {"multi_match": {"query": query, "fields": ["title^2", "content"]}},
                "filter": [{"term": {"locale": locale}}, {"term": {"status": "published"}}],
            }
        },
    )
    return [{**hit["_source"], "score": hit["_score"]} for hit in resp["hits"]["hits"]]
