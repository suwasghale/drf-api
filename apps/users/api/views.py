from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from apps.users.models import Country, State, Address
from apps.users.api.serializers import (
    CountrySerializer,
    StateSerializer,
    AddressSerializer,
)
from apps.users.api.permissions import IsOwner, IsVendorOrStaffOrReadOnly, IsStaffOrSuperAdmin, CanViewOrder

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Countries: public read-only.
    - Example: GET /api/v2/countries/
    """
    queryset = Country.objects.all().order_by("name")
    serializer_class = CountrySerializer
    permission_classes = []  # anyone can read


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    States: public read-only, filterable by country.
    - Example: GET /api/v2/states/?country=<country_id>
    """
    queryset = State.objects.select_related("country").all().order_by("name")
    serializer_class = StateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country__id"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    permission_classes = []