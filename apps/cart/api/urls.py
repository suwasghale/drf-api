from rest_framework.routers import DefaultRouter
from django.urls import path, include
from apps.cart.api.views import CartViewSet

router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
