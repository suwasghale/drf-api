from rest_framework import exceptions
from rest_framework.permissions import IsAuthenticated

class OwnerOrStaffMixin:
    """
    Intended to be mixed into a ModelViewSet.
    - list: staff sees all, others filtered via get_queryset()
    - retrieve: permission check via check_object_permissions
    - create: request.user used as owner unless staff explicitly provides owner_id
    - update/destroy: enforced by permissions (IsOwner or IsStaffOrSuperAdmin)
    """
    def perform_create(self, serializer):
        # If staff provided explicit owner (e.g., user_id) the serializer should accept it,
        # otherwise set current user as owner.
        request = self.request
        if hasattr(serializer.validated_data, "get") and serializer.validated_data.get("user"):
            # serializer already set user via user_id; ensure only staff can create for other users
            if not request.user.is_staff and serializer.validated_data.get("user") != request.user:
                raise exceptions.PermissionDenied("Not permitted to create for other users.")
        else:
            serializer.save(user=request.user)