import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.pages.models import Page, PageType

from .models import BlockType, PageBlock

User = get_user_model()


@pytest.fixture
def page_type(db):
    return PageType.objects.create(name="Blocks Type", slug="blocks-type", is_system=False)


@pytest.fixture
def block_type(db):
    # BlockType.name is unique and the registry is seeded by a data migration, so
    # this needs a name that cannot collide with a shipped block type.
    return BlockType.objects.create(
        name="Reorder Test Block",
        slug="reorder-test-block",
        category="content",
        prop_schema={"fields": []},
    )


@pytest.fixture
def client(db):
    User.objects.create_superuser(email="blocks@test.local", password="S3cure!2026")
    c = APIClient()
    login = c.post("/api/v1/auth/login/", {"email": "blocks@test.local", "password": "S3cure!2026"})
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return c


@pytest.fixture
def page(page_type):
    return Page.objects.create(slug="blocks-host", page_type=page_type)


def _mk(page, block_type, count):
    return [
        PageBlock.objects.create(page=page, block_type=block_type, order=i, props={})
        for i in range(count)
    ]


@pytest.mark.django_db
class TestBlockReorder:
    """Regression: reorder walked the raw request body and called .update() per
    item. Malformed payloads raised out of the view as 500s, unknown ids silently
    no-opped while still returning {"status": "ok"}, and nothing scoped the update
    to a single page — so one call could reorder and reparent another page's blocks."""

    def test_reorder_applies_new_order(self, client, page, block_type):
        blocks = _mk(page, block_type, 3)
        want = [b.id for b in reversed(blocks)]

        resp = client.post(
            "/api/v1/page-blocks/reorder/",
            [{"id": bid, "order": i, "parent": None} for i, bid in enumerate(want)],
            format="json",
        )

        assert resp.status_code == 200
        got = list(
            PageBlock.objects.filter(page=page).order_by("order").values_list("id", flat=True)
        )
        assert got == want

    @pytest.mark.parametrize(
        "payload",
        [
            {"not": "a list"},
            [{"order": 0}],
            [{"id": 1, "order": "abc"}],
            ["not-an-object"],
            [{"id": "x", "order": 0}],
        ],
    )
    def test_malformed_payload_is_400_not_500(self, client, payload):
        resp = client.post("/api/v1/page-blocks/reorder/", payload, format="json")
        assert resp.status_code == 400

    def test_unknown_block_id_rejected(self, client):
        resp = client.post(
            "/api/v1/page-blocks/reorder/",
            [{"id": 99999999, "order": 0, "parent": None}],
            format="json",
        )
        assert resp.status_code == 400
        assert "Unknown block ids" in resp.data["detail"]

    def test_cannot_reorder_blocks_across_pages(self, client, page, page_type, block_type):
        other = Page.objects.create(slug="other-host", page_type=page_type)
        a = PageBlock.objects.create(page=page, block_type=block_type, order=0, props={})
        b = PageBlock.objects.create(page=other, block_type=block_type, order=0, props={})

        resp = client.post(
            "/api/v1/page-blocks/reorder/",
            [{"id": a.id, "order": 0, "parent": None}, {"id": b.id, "order": 1, "parent": None}],
            format="json",
        )

        assert resp.status_code == 400
        b.refresh_from_db()
        assert b.order == 0  # untouched

    def test_parent_must_belong_to_same_page(self, client, page, page_type, block_type):
        other = Page.objects.create(slug="other-host-2", page_type=page_type)
        mine = PageBlock.objects.create(page=page, block_type=block_type, order=0, props={})
        foreign_parent = PageBlock.objects.create(page=other, block_type=block_type, order=0, props={})

        resp = client.post(
            "/api/v1/page-blocks/reorder/",
            [{"id": mine.id, "order": 0, "parent": foreign_parent.id}],
            format="json",
        )

        assert resp.status_code == 400
        mine.refresh_from_db()
        assert mine.parent_id is None

    def test_empty_payload_is_noop(self, client):
        resp = client.post("/api/v1/page-blocks/reorder/", [], format="json")
        assert resp.status_code == 200
        assert resp.data["updated"] == 0


@pytest.mark.django_db
class TestBlockFiltering:
    """Regression: `page` was declared in filterset_fields but DRF's paginator owns
    `?page=`, so `?page=3` was parsed as "results page 3" and 404'd instead of
    filtering. The FK filter is exposed as `page_id`."""

    def test_page_id_filter_returns_only_that_pages_blocks(self, client, page, page_type, block_type):
        other = Page.objects.create(slug="filter-other", page_type=page_type)
        _mk(page, block_type, 2)
        PageBlock.objects.create(page=other, block_type=block_type, order=0, props={})

        resp = client.get(f"/api/v1/page-blocks/?page_id={page.id}")

        assert resp.status_code == 200
        assert resp.data["count"] == 2
        assert {b["page"] for b in resp.data["results"]} == {page.id}


@pytest.mark.django_db
class TestPageTypeBlockRestrictions:
    """PageType.allowed_block_types is blank=True on every existing page type —
    unrestricted, so this must not change behavior for page types that never
    set it. Only once a page type actually scopes the set should creation of an
    out-of-scope block get rejected."""

    def test_unrestricted_page_type_accepts_any_block(self, client, page_type, block_type):
        page = Page.objects.create(slug="unrestricted-host", page_type=page_type)

        resp = client.post(
            "/api/v1/page-blocks/",
            {"page": page.id, "block_type": block_type.id, "order": 0, "props": {}},
            format="json",
        )

        assert resp.status_code == 201

    def test_scoped_page_type_rejects_disallowed_block(self, client, page_type, block_type):
        other_block_type = BlockType.objects.create(
            name="Other Restricted Block", slug="other-restricted-block", category="content", prop_schema={"fields": []}
        )
        page_type.allowed_block_types.add(block_type)  # only `block_type` is allowed
        page = Page.objects.create(slug="scoped-host", page_type=page_type)

        resp = client.post(
            "/api/v1/page-blocks/",
            {"page": page.id, "block_type": other_block_type.id, "order": 0, "props": {}},
            format="json",
        )

        assert resp.status_code == 400
        assert "block_type" in resp.data

    def test_scoped_page_type_accepts_allowed_block(self, client, page_type, block_type):
        page_type.allowed_block_types.add(block_type)
        page = Page.objects.create(slug="scoped-host-2", page_type=page_type)

        resp = client.post(
            "/api/v1/page-blocks/",
            {"page": page.id, "block_type": block_type.id, "order": 0, "props": {}},
            format="json",
        )

        assert resp.status_code == 201

    def test_partial_update_not_touching_block_type_still_validated_against_instance(self, client, page_type, block_type):
        """A reorder-only PATCH (order/props, no block_type in the payload) must
        still be checked against the existing block_type — falling back to
        self.instance is what makes that work."""
        other_page_type = PageType.objects.create(name="Other Page Type", slug="other-page-type")
        other_page_type.allowed_block_types.add(block_type)  # allowed initially
        page = Page.objects.create(slug="reorder-host", page_type=other_page_type)
        block = PageBlock.objects.create(page=page, block_type=block_type, order=0, props={})

        resp = client.patch(f"/api/v1/page-blocks/{block.id}/", {"order": 1}, format="json")

        assert resp.status_code == 200
