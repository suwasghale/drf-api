from rest_framework import permissions

class RoleRequired(permissions.BasePermission):
    """
    Base class for role-based permissions.
    """
    required_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, "role", None) in self.required_roles
        )


class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to superadmins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsStaff(permissions.BasePermission):
    """
    Allows access only to staff members.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsVendor(RoleRequired):
    """
    Allows access only to vendors.
    """
    required_roles = ['VENDOR']


class IsUser(RoleRequired):
    """
    Allows access only to regular users.
    """
    required_roles = ['USER']


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to allow owners of an object to edit it.
    Checks multiple common ownership patterns.
    """

    owner_attrs = ["user", "owner", "created_by"]

    def has_object_permission(self, request, view, obj):
        # Allow read-only access to anyone.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check for multiple possible owner fields.
        for attr in self.owner_attrs:
            if hasattr(obj, attr):
                return getattr(obj, attr) == request.user

        return False


class IsVendorOrStaffOrReadOnly(permissions.BasePermission):
    """
    Vendors and staff can modify; others have read-only access.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated and
            (request.user.is_staff or getattr(request.user, "role", None) == 'VENDOR')
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user

        if user.is_staff:
            return True

        if getattr(user, "role", None) == 'VENDOR':
            return getattr(obj, 'vendor', None) == user

        return False


class IsStaffOrSuperAdmin(permissions.BasePermission):
    """
    Allows access to staff or superadmins.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class CanViewOrder(permissions.BasePermission):
    """
    Object-level permission: users see their own orders,
    vendors see orders containing their products,
    staff/superadmins see all.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        if getattr(user, "role", None) == 'USER':
            return obj.user == user

        if user.role == 'VENDOR':
            return obj.items.filter(product__vendor=user).exists()

        return False
