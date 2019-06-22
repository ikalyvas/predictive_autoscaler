from .views import MetricsViewsSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(prefix='metrics', viewset=MetricsViewsSet)
urlpatterns = router.urls
