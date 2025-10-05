from rest_framework.routers import DefaultRouter
from apps.shipments.api.views import ShipmentViewSet

router = DefaultRouter()
router.register("shipments", ShipmentViewSet, basename="shipment")

urlpatterns = router.urls
