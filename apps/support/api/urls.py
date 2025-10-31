# apps/support/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.support.api.views import TicketViewSet, TicketMessageViewSet

router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="tickets")
router.register(r"messages", TicketMessageViewSet, basename="ticket-messages")

urlpatterns = [
    path("", include(router.urls)),
]
