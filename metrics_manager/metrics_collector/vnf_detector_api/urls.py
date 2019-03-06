from .views import LayerViewSet
from rest_framework import routers

router = routers.DefaultRouter()

router.register('vnfs', LayerViewSet, base_name='vnfs')

urlpatterns = router.urls
