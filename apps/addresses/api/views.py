from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.addresses.models import Country, State, Address
from apps.addresses.api.serializers import (
    CountrySerializer,
    StateSerializer,
    AddressSerializer,
)
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.core.permissions import (
    IsOwner,
    IsStaffOrSuperAdmin,
)


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only view for countries.
    """
    queryset = Country.objects.all().order_by("name")
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only view for states, filterable by country.
    """
    queryset = State.objects.select_related("country").all().order_by("name")
    serializer_class = StateSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country__id"]
    search_fields = ["name"]
    ordering_fields = ["name"]

    permission_classes = [AllowAny]


class AddressViewSet(viewsets.ModelViewSet):
    """
    Address management:
    - Normal users → full CRUD on their own addresses.
    - Staff/superadmins → manage all users’ addresses.
    - Default address logic handled atomically.
    """
    queryset = Address.objects.select_related("country", "state", "user")
    serializer_class = AddressSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["address_type", "city", "country__id", "is_default"]
    search_fields = ["street_address", "recipient_name", "city"]
    ordering_fields = ["created_at", "city", "is_default"]

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    # ---------------------------------------------------------------------
    # Permission Handling
    # ---------------------------------------------------------------------
    def get_permissions(self):

        # Public endpoints handled separately
        if self.action in ["default", "set_default", "list", "retrieve", "create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated()]

        return super().get_permissions()

    def get_queryset(self):
        """
        Staff sees all records.
        Users see only their own addresses.
        """
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return self.queryset

        return self.queryset.filter(user=user)

    # ---------------------------------------------------------------------
    # CRUD Overrides
    # ---------------------------------------------------------------------

    def perform_destroy(self, instance):
        """
        When deleting a default address:
        - promote another address as default (latest created).
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

    # ---------------------------------------------------------------------
    # Custom Endpoints
    # ---------------------------------------------------------------------

    @action(
        detail=False,
        methods=["get"],
        url_path="default",
        permission_classes=[IsAuthenticated]
    )
    def default(self, request):
        """
        Get the current user's default address.
        """
        addr = Address.objects.filter(user=request.user, is_default=True).first()

        if not addr:
            return Response(
                {"detail": "No default address found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(self.get_serializer(addr).data)

    @action(
        detail=False,
        methods=["post"],
        url_path="set-default",
        permission_classes=[IsAuthenticated]
    )
    def set_default(self, request):
        """
        Set an address as default.
        Payload:
        {
            "address_id": <id>
        }
        """
        address_id = request.data.get("address_id")

        if not address_id:
            return Response({"detail": "address_id is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            addr = Address.objects.select_related("user").get(pk=address_id)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # Ownership check – staff/superadmins bypass
        if not (request.user.is_staff or request.user.is_superuser):
            if addr.user != request.user:
                return Response({"detail": "Forbidden."},
                                status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            Address.objects.filter(user=addr.user, is_default=True).exclude(pk=addr.pk).update(is_default=False)
            addr.is_default = True
            addr.save(update_fields=["is_default"])

        return Response(self.get_serializer(addr).data)
