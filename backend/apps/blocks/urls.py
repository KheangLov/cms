from rest_framework.routers import DefaultRouter

from .views import BlockTypeViewSet, PageBlockViewSet, PostBlockViewSet

router = DefaultRouter()
router.register("block-types", BlockTypeViewSet, basename="block-type")
router.register("page-blocks", PageBlockViewSet, basename="page-block")
router.register("post-blocks", PostBlockViewSet, basename="post-block")

urlpatterns = router.urls
