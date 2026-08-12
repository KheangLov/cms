from rest_framework.routers import DefaultRouter

from .views import PageTypeViewSet, PageViewSet

router = DefaultRouter()
router.register("pages", PageViewSet, basename="page")
router.register("page-types", PageTypeViewSet, basename="page-type")

urlpatterns = router.urls
