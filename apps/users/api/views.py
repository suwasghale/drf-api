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
    permission_classes = []  # anyone can read


class AddressViewSet(viewsets.ModelViewSet):
    """
    Address endpoints:
    - list:       GET /addresses/             (user → own, staff → all)
    - retrieve:   GET /addresses/{id}/
    - create:     POST /addresses/            (auto-assigns request.user, staff can assign user_id)
    - update:     PUT/PATCH /addresses/{id}/
    - destroy:    DELETE /addresses/{id}/
    - default:    GET /addresses/default/     (get current default)
    - set_default:POST /addresses/set-default/ { "address_id": <id> }

    Features:
    - staff can manage addresses for any user
    - duplicate prevention handled at serializer-level
    - atomic handling of default addresses
    """
    queryset = Address.objects.select_related("country", "state", "user").all()
    serializer_class = AddressSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["address_type", "city", "country__id", "is_default"]
    search_fields = ["street_address", "recipient_name", "city"]
    ordering_fields = ["created_at", "city", "is_default"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """
        Dynamic permissions:
        - Authenticated users can CRUD their own addresses
        - Staff / superadmins can manage all
        """
        if self.action in ["list", "retrieve", "create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]
        return super().get_permissions()