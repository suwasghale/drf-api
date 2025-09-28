from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated

from apps.addresses.models import Country, State, Address
from apps.addresses.api.serializers import (
    CountrySerializer,
    StateSerializer,
    AddressSerializer,
)


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
    
    def get_queryset(self):
        """Limit normal users to their own addresses."""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return self.queryset
        return self.queryset.filter(user=user)
    
    def perform_destroy(self, instance):
        """
        If deleting a default address, promote another address of the same user to default.
        """
        user = instance.user
        was_default = instance.is_default
        with transaction.atomic():
            instance.delete()
            if was_default:
                replacement = Address.objects.filter(user=user).order_by("-created_at").first()
                if replacement:
                    replacement.is_default = True
                    replacement.save(update_fields=["is_default"])


    @action(detail=False, methods=["get"], url_path="default", permission_classes=[IsAuthenticated])
    def default(self, request):
        """
        Fetch the user's default address.
        """
        addr = Address.objects.filter(user=request.user, is_default=True).first()
        if not addr:
            return Response({"detail": "No default address set"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(addr).data)

   

    @action(detail=False, methods=["post"], url_path="set-default", permission_classes=[IsAuthenticated])
    def set_default(self, request):
        """
        Set an address as default.
        Payload: { "address_id": <id> }
        """
        address_id = request.data.get("address_id")
        if not address_id:
            return Response({"detail": "address_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found"}, status=status.HTTP_404_NOT_FOUND)

        # Ensure ownership unless staff/superadmin
        if not (request.user.is_staff or request.user.is_superuser or address.user == request.user):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            Address.objects.filter(user=address.user, is_default=True).exclude(pk=address.pk).update(is_default=False)
            address.is_default = True
            address.save(update_fields=["is_default"])

        return Response(self.get_serializer(address).data, status=status.HTTP_200_OK)