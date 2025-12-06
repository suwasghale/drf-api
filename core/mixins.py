from rest_framework import exceptions

class OwnerOrStaffMixin:
    """
    A generic mixin for ModelViewSets that enforces:
    - Vendors/normal users: can create only for themselves.
    - Staff/superadmin: can create for anyone.
    - perform_update: object-level permissions still apply via DRF permissions.
    - perform_destroy: DRF permissions decide.
    
    Requirements:
    - Your model must contain either 'user' or 'owner' FK.
    - Your User model must have role helpers: is_vendor(), is_staff_user(), is_superadmin().
    """

    owner_field_names = ["user", "owner"]  # automatically detect FK field

    def _get_owner_field_name(self):
        """Detect if serializer/model uses 'user' or 'owner'."""
        for field in self.owner_field_names:
            if field in getattr(self.get_serializer().Meta, "fields", []):
                return field
        return None

    def perform_create(self, serializer):
        """
        Creation rules:
        - If vendor/normal user → they cannot assign other users as owners.
        - If staff/superadmin → they can set owner manually.
        - If owner not passed at all → set request.user automatically.
        """
        request = self.request
        user = request.user
        owner_field = self._get_owner_field_name()

        if owner_field is None:
            # No owner/user field in serializer → nothing special to enforce.
            serializer.save()
            return

        incoming_data = serializer.validated_data

        # If owner was explicitly provided in data
        if owner_field in incoming_data:
            incoming_owner = incoming_data[owner_field]

            # Vendor or normal user cannot assign ownership to others
            if not (user.is_staff or user.is_superadmin()):
                if incoming_owner != user:
                    raise exceptions.PermissionDenied(
                        "You do not have permission to assign another user as owner."
                    )

            # Staff/superadmin: allowed to assign other owners
            serializer.save()
            return

        # If owner not provided → default to current user
        serializer.save(**{owner_field: user})

    def perform_update(self, serializer):
        """
        Updates are governed by DRF object-level permissions.
        Vendors cannot change the owner field even if sent in request.
        """
        request = self.request
        user = request.user
        owner_field = self._get_owner_field_name()

        if owner_field and owner_field in serializer.validated_data:
            # User tries to modify owner field
            if not (user.is_staff or user.is_superadmin()):
                raise exceptions.PermissionDenied(
                    "You do not have permission to reassign the owner."
                )

        serializer.save()
