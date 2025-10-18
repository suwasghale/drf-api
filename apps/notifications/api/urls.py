from rest_framework.routers import DefaultRouter
from apps.notifications.api.views import NotificationViewSet

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notifications")

urlpatterns = router.urls
