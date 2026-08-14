import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.blocks.models import BlockType, PageBlock
from apps.posts.models import Post
from apps.settings_app.models import Setting

from .models import Page, PageType

User = get_user_model()


@pytest.fixture
def page_type(db):
    return PageType.objects.create(name="Test Type", slug="test-type", is_system=False)


def _authed_client(email="admin@test.local"):
    User.objects.create_superuser(email=email, password="S3cure!2026")
    client = APIClient()
    login = client.post("/api/v1/auth/login/", {"email": email, "password": "S3cure!2026"})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    return client


@pytest.mark.django_db
class TestPagePermissions:
    """CMS_BUILD_PROMPT.md §5.4 — public read for published content, permission-
    gated writes."""

    def test_anonymous_can_read_published(self, page_type):
        Page.objects.create(slug="public-page", page_type=page_type, status="published")
        resp = APIClient().get("/api/v1/pages/")
        assert resp.status_code == 200
        assert any(p["slug"] == "public-page" for p in resp.data["results"])

    def test_anonymous_cannot_see_draft(self, page_type):
        Page.objects.create(slug="draft-page", page_type=page_type, status="draft")
        resp = APIClient().get("/api/v1/pages/")
        assert not any(p["slug"] == "draft-page" for p in resp.data["results"])

    def test_anonymous_cannot_create(self, page_type):
        resp = APIClient().post("/api/v1/pages/", {"slug": "x", "page_type": page_type.id})
        assert resp.status_code == 401

    def test_superuser_can_create(self, page_type):
        client = _authed_client()
        resp = client.post("/api/v1/pages/", {"slug": "new-page", "page_type": page_type.id})
        assert resp.status_code == 201


@pytest.mark.django_db
class TestSoftDelete:
    """CMS_BUILD_PROMPT.md §5.9 — delete sets is_deleted, doesn't remove the row;
    restore brings it back through the default manager's visibility."""

    def test_soft_delete_and_restore(self, page_type):
        client = _authed_client("admin2@test.local")
        create = client.post("/api/v1/pages/", {"slug": "deletable", "page_type": page_type.id})
        page_id = create.data["id"]

        resp = client.delete(f"/api/v1/pages/{page_id}/")
        assert resp.status_code == 204
        assert not Page.objects.filter(id=page_id).exists()
        assert Page.all_objects.filter(id=page_id).exists()

        resp = client.post(f"/api/v1/pages/{page_id}/restore/")
        assert resp.status_code == 200
        assert Page.objects.filter(id=page_id).exists()


@pytest.mark.django_db
class TestPageHierarchyCycles:
    """Regression: PageSerializer exposed `parent` with no validation, so a single
    PATCH could make a page its own parent. That silently un-rooted the page
    (ResolveView walks down from parent=None, so the URL stopped resolving) and
    made Page.full_path() loop forever, growing a list until the worker died."""

    def test_page_cannot_be_its_own_parent(self, page_type):
        client = _authed_client("cycle1@test.local")
        page_id = client.post("/api/v1/pages/", {"slug": "self-parent", "page_type": page_type.id}).data["id"]

        resp = client.patch(f"/api/v1/pages/{page_id}/", {"parent": page_id}, format="json")

        assert resp.status_code == 400
        assert "parent" in resp.data
        assert Page.objects.get(id=page_id).parent_id is None

    def test_page_cannot_be_parented_to_its_own_descendant(self, page_type):
        client = _authed_client("cycle2@test.local")
        root = client.post("/api/v1/pages/", {"slug": "root", "page_type": page_type.id}).data["id"]
        child = client.post(
            "/api/v1/pages/", {"slug": "child", "page_type": page_type.id, "parent": root}
        ).data["id"]
        grandchild = client.post(
            "/api/v1/pages/", {"slug": "grandchild", "page_type": page_type.id, "parent": child}
        ).data["id"]

        resp = client.patch(f"/api/v1/pages/{root}/", {"parent": grandchild}, format="json")

        assert resp.status_code == 400
        assert Page.objects.get(id=root).parent_id is None

    def test_valid_reparent_still_allowed(self, page_type):
        client = _authed_client("cycle3@test.local")
        a = client.post("/api/v1/pages/", {"slug": "branch-a", "page_type": page_type.id}).data["id"]
        b = client.post("/api/v1/pages/", {"slug": "branch-b", "page_type": page_type.id}).data["id"]

        resp = client.patch(f"/api/v1/pages/{a}/", {"parent": b}, format="json")

        assert resp.status_code == 200
        assert Page.objects.get(id=a).parent_id == b

    def test_full_path_terminates_on_preexisting_cycle(self, page_type):
        """Data written before the serializer guard (or via shell/SQL) must not hang."""
        page = Page.objects.create(slug="corrupt", page_type=page_type)
        Page.objects.filter(pk=page.pk).update(parent=page)  # bypass validation
        page.refresh_from_db()

        assert page.full_path() == "corrupt"

    def test_full_path_builds_nested_path(self, page_type):
        root = Page.objects.create(slug="docs", page_type=page_type)
        child = Page.objects.create(slug="guide", page_type=page_type, parent=root)

        assert child.full_path() == "docs/guide"


@pytest.mark.django_db
class TestResolver:
    """Posts live at a fixed /post/<slug> namespace, independent of the page
    tree (CMS_BUILD_PROMPT.md §5.1); Pages stay hierarchical at root. `post` is
    reserved for the namespace, so a /post/<slug> request never falls back to
    matching a page."""

    def test_resolves_post_under_post_prefix(self):
        Post.objects.create(slug="hello-world", status="published")

        resp = APIClient().get("/api/v1/resolve/", {"path": "post/hello-world"})

        assert resp.status_code == 200
        assert resp.data["type"] == "post"
        assert resp.data["data"]["slug"] == "hello-world"

    def test_bare_slug_no_longer_resolves_a_post(self):
        """Regression: the resolver used to match a post by its last path
        segment regardless of prefix, so a post was reachable at both its bare
        slug and any nonsense prefix ending in that slug."""
        Post.objects.create(slug="hello-world", status="published")

        resp = APIClient().get("/api/v1/resolve/", {"path": "hello-world"})

        assert resp.status_code == 404

    def test_unpublished_post_404s_even_under_post_prefix(self):
        Post.objects.create(slug="draft-post", status="draft")

        resp = APIClient().get("/api/v1/resolve/", {"path": "post/draft-post"})

        assert resp.status_code == 404

    def test_unknown_slug_under_post_prefix_404s_without_falling_back_to_pages(self, page_type):
        """`post` is a reserved namespace root — even if a page happened to be
        parented there, /post/<slug> must not silently resolve to it."""
        root = Page.objects.create(slug="post", page_type=page_type, status="published")
        Page.objects.create(slug="not-a-post", page_type=page_type, status="published", parent=root)

        resp = APIClient().get("/api/v1/resolve/", {"path": "post/not-a-post"})

        assert resp.status_code == 404

    def test_page_still_resolves_at_root_slug(self, page_type):
        Page.objects.create(slug="about", page_type=page_type, status="published")

        resp = APIClient().get("/api/v1/resolve/", {"path": "about"})

        assert resp.status_code == 200
        assert resp.data["type"] == "page"
        assert resp.data["data"]["slug"] == "about"

    def test_page_still_resolves_hierarchically(self, page_type):
        root = Page.objects.create(slug="docs", page_type=page_type, status="published")
        Page.objects.create(slug="guide", page_type=page_type, status="published", parent=root)

        resp = APIClient().get("/api/v1/resolve/", {"path": "docs/guide"})

        assert resp.status_code == 200
        assert resp.data["type"] == "page"
        assert resp.data["data"]["full_path"] == "docs/guide"

    def test_root_path_resolves_configured_homepage(self, page_type):
        home = Page.objects.create(slug="home", page_type=page_type, status="published")
        setting = Setting(key="homepage_page_id", category="general")
        setting.value = home.id
        setting.save()

        resp = APIClient().get("/api/v1/resolve/", {"path": ""})

        assert resp.status_code == 200
        assert resp.data["type"] == "page"
        assert resp.data["data"]["slug"] == "home"

    def test_root_path_404s_when_no_homepage_configured(self):
        resp = APIClient().get("/api/v1/resolve/", {"path": ""})

        assert resp.status_code == 404

    def test_root_path_404s_when_homepage_is_unpublished(self, page_type):
        home = Page.objects.create(slug="home", page_type=page_type, status="draft")
        setting = Setting(key="homepage_page_id", category="general")
        setting.value = home.id
        setting.save()

        resp = APIClient().get("/api/v1/resolve/", {"path": ""})

        assert resp.status_code == 404

    def test_homepage_still_reachable_at_its_own_slug(self, page_type):
        """Setting a page as the homepage doesn't remove its normal URL — same as
        WordPress: a static front page keeps its own permalink too."""
        home = Page.objects.create(slug="home", page_type=page_type, status="published")
        setting = Setting(key="homepage_page_id", category="general")
        setting.value = home.id
        setting.save()

        resp = APIClient().get("/api/v1/resolve/", {"path": "home"})

        assert resp.status_code == 200
        assert resp.data["data"]["slug"] == "home"


@pytest.mark.django_db
class TestSiteChrome:
    """Navbar/Footer are ordinary blocks on one reserved Page, picked via the
    site_chrome_page_id Setting — mirrors the homepage_page_id pattern."""

    def test_no_setting_returns_empty_blocks_not_error(self):
        resp = APIClient().get("/api/v1/site-chrome/")

        assert resp.status_code == 200
        assert resp.data["blocks"] == []

    def test_returns_navbar_and_footer_blocks_with_resolved_links(self, page_type):
        navbar_type = BlockType.objects.get(slug="navbar")
        about = Page.objects.create(slug="about", page_type=page_type, status="published")
        chrome_page = Page.objects.create(slug="site-chrome", page_type=page_type, status="published")
        PageBlock.objects.create(
            page=chrome_page,
            block_type=navbar_type,
            order=0,
            props={"logoText": {"en": "Ember Co"}, "links": [{"label": "About", "pageId": about.id}]},
        )
        setting = Setting(key="site_chrome_page_id", category="general")
        setting.value = chrome_page.id
        setting.save()

        resp = APIClient().get("/api/v1/site-chrome/")

        assert resp.status_code == 200
        assert len(resp.data["blocks"]) == 1
        link = resp.data["blocks"][0]["props"]["links"][0]
        assert link["resolvedUrl"] == "/about"

    def test_link_with_raw_url_is_used_as_is(self, page_type):
        navbar_type = BlockType.objects.get(slug="navbar")
        chrome_page = Page.objects.create(slug="site-chrome", page_type=page_type, status="published")
        PageBlock.objects.create(
            page=chrome_page, block_type=navbar_type, order=0,
            props={"links": [{"label": "External", "url": "https://example.com"}]},
        )
        setting = Setting(key="site_chrome_page_id", category="general")
        setting.value = chrome_page.id
        setting.save()

        resp = APIClient().get("/api/v1/site-chrome/")

        assert resp.data["blocks"][0]["props"]["links"][0]["resolvedUrl"] == "https://example.com"

    def test_link_to_missing_page_resolves_to_none(self, page_type):
        navbar_type = BlockType.objects.get(slug="navbar")
        chrome_page = Page.objects.create(slug="site-chrome", page_type=page_type, status="published")
        PageBlock.objects.create(
            page=chrome_page, block_type=navbar_type, order=0,
            props={"links": [{"label": "Gone", "pageId": 999999}]},
        )
        setting = Setting(key="site_chrome_page_id", category="general")
        setting.value = chrome_page.id
        setting.save()

        resp = APIClient().get("/api/v1/site-chrome/")

        assert resp.data["blocks"][0]["props"]["links"][0]["resolvedUrl"] is None


@pytest.mark.django_db
class TestPagePresentationFields:
    """Per-page container width + background, independent of block content."""

    def test_defaults_to_default_width_no_background(self, page_type):
        page = Page.objects.create(slug="plain", page_type=page_type)

        assert page.container_width == "default"
        assert page.background_color == ""
        assert page.background_image_url == ""

    def test_can_be_set_through_the_api(self, page_type):
        client = _authed_client("presentation@test.local")
        page_id = client.post("/api/v1/pages/", {"slug": "styled", "page_type": page_type.id}).data["id"]

        resp = client.patch(
            f"/api/v1/pages/{page_id}/",
            {"container_width": "wide", "background_color": "#111111", "background_image_url": "/img.jpg"},
            format="json",
        )

        assert resp.status_code == 200
        page = Page.objects.get(id=page_id)
        assert page.container_width == "wide"
        assert page.background_color == "#111111"
        assert page.background_image_url == "/img.jpg"


@pytest.mark.django_db
class TestDefaultBlocks:
    """PageType.default_blocks auto-populates a *new* page as a starting point
    — applied once at creation, never touching pages that already exist."""

    def test_new_page_gets_preset_blocks(self, page_type):
        hero_type = BlockType.objects.get(slug="hero")
        text_type = BlockType.objects.get(slug="text-section")
        page_type.default_blocks = [
            {"block_type": "hero", "props": {"heading": {"en": "Hi"}}},
            {"block_type": "text-section", "props": {"heading": {"en": "More"}}},
        ]
        page_type.save(update_fields=["default_blocks"])
        client = _authed_client("presets1@test.local")

        resp = client.post("/api/v1/pages/", {"slug": "with-presets", "page_type": page_type.id})

        assert resp.status_code == 201
        page = Page.objects.get(id=resp.data["id"])
        blocks = list(page.blocks.order_by("order"))
        assert [b.block_type_id for b in blocks] == [hero_type.id, text_type.id]
        assert blocks[0].props["heading"]["en"] == "Hi"

    def test_nested_children_are_created_with_correct_parent(self, page_type):
        page_type.default_blocks = [
            {
                "block_type": "columns",
                "props": {"columnCount": 2},
                "children": [
                    {"block_type": "text-section", "props": {"heading": {"en": "Left"}}},
                    {"block_type": "text-section", "props": {"heading": {"en": "Right"}}},
                ],
            },
        ]
        page_type.save(update_fields=["default_blocks"])
        client = _authed_client("presets2@test.local")

        resp = client.post("/api/v1/pages/", {"slug": "with-nested-presets", "page_type": page_type.id})

        page = Page.objects.get(id=resp.data["id"])
        columns_block = page.blocks.get(parent__isnull=True)
        children = list(columns_block.children.order_by("order"))
        assert len(children) == 2
        assert children[0].props["heading"]["en"] == "Left"
        assert children[1].props["heading"]["en"] == "Right"

    def test_empty_default_blocks_creates_nothing(self, page_type):
        client = _authed_client("presets3@test.local")

        resp = client.post("/api/v1/pages/", {"slug": "no-presets", "page_type": page_type.id})

        page = Page.objects.get(id=resp.data["id"])
        assert page.blocks.count() == 0

    def test_unknown_block_type_slug_is_skipped_not_fatal(self, page_type):
        page_type.default_blocks = [
            {"block_type": "does-not-exist", "props": {}},
            {"block_type": "hero", "props": {}},
        ]
        page_type.save(update_fields=["default_blocks"])
        client = _authed_client("presets4@test.local")

        resp = client.post("/api/v1/pages/", {"slug": "partial-presets", "page_type": page_type.id})

        assert resp.status_code == 201
        page = Page.objects.get(id=resp.data["id"])
        assert page.blocks.count() == 1
        assert page.blocks.first().block_type.slug == "hero"

    def test_existing_page_is_not_touched_when_preset_changes(self, page_type):
        client = _authed_client("presets5@test.local")
        page_id = client.post("/api/v1/pages/", {"slug": "already-exists", "page_type": page_type.id}).data["id"]
        assert Page.objects.get(id=page_id).blocks.count() == 0

        page_type.default_blocks = [{"block_type": "hero", "props": {}}]
        page_type.save(update_fields=["default_blocks"])

        assert Page.objects.get(id=page_id).blocks.count() == 0
