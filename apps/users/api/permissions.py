from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------------------------------------
# Base Permissions
# ---------------------------------------------------------

class RoleRequired(permissions.BasePermission):
    """
    Base class for role-based permissions.
    Subclasses must define 'required_roles'.
    """
    required_roles: list[str] = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "role", None) in self.required_roles
        )


class OwnershipRequired(permissions.BasePermission):
    """
    Base class for object-level ownership checks.
    Checks multiple common ownership attribute names.
    """

    owner_attrs = ["user", "owner", "created_by", "author"]

    def is_owner(self, obj, user):
        for attr in self.owner_attrs:
            if hasattr(obj, attr):
                return getattr(obj, attr) == user
        return False


# ---------------------------------------------------------
# Role-Based Permissions
# ---------------------------------------------------------

class IsSuperAdmin(permissions.BasePermission):
    """Access allowed only for Django superusers."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsStaff(permissions.BasePermission):
    """Access allowed only for Django staff."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsVendor(RoleRequired):
    """Access allowed only to vendors."""
    required_roles = [User.Roles.VENDOR]


class IsUser(RoleRequired):
    """Access allowed only to regular users."""
    required_roles = [User.Roles.USER]


# ---------------------------------------------------------
# Ownership / Object-Level Permissions
# ---------------------------------------------------------

class IsOwner(OwnershipRequired):
    """
    Allows owners to edit an object.
    Read-only access is open for all.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only always allowed
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write allowed only for the owner
        return self.is_owner(obj, request.user)


class CanManageAddress(permissions.BasePermission):
    """
    Only the address owner, staff, or superadmin can view/edit addresses.
    Addresses are sensitive PII.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        # Read-only allowed if owner or staff
        if request.method in permissions.SAFE_METHODS:
            return obj.user == user or user.is_staff or user.is_superuser

        # Write allowed only to owner or staff/superadmin
        return obj.user == user or user.is_staff or user.is_superuser


# ---------------------------------------------------------
# Vendor & Staff Mixed Permissions
# ---------------------------------------------------------

class IsVendorOrStaffOrReadOnly(permissions.BasePermission):
    """
    Staff and vendors can write.
    Everyone else has read-only access.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.is_staff or user.role == User.Roles.VENDOR

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user

        # Staff can edit anything
        if user.is_staff:
            return True

        # Vendor can edit only their own objects
        if user.role == User.Roles.VENDOR:
            if hasattr(obj, "vendor"):
                return obj.vendor == user
            return False

        return False


class IsStaffOrSuperAdmin(permissions.BasePermission):
    """
    Allows access only to staff or superadmins.
    """

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)


# ---------------------------------------------------------
# Order Permissions
# ---------------------------------------------------------

class CanViewOrder(permissions.BasePermission):
    """
    Users can view only their own orders.
    Vendors can view orders containing their products.
    Staff/superadmin can view all orders.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        # Global access
        if user.is_superuser or user.is_staff:
            return True

        # Users see only their own orders
        if user.role == User.Roles.USER:
            return obj.user == user

        # Vendors: view orders that include their products
        if user.role == User.Roles.VENDOR:
            if hasattr(obj, "items"):
                return obj.items.filter(product__vendor=user).exists()

        return False
