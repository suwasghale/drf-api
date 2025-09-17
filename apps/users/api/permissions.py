from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to superadmins.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class IsStaff(permissions.BasePermission):
    """
    Allows access only to staff (admins).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class IsVendor(permissions.BasePermission):
    """
    Allows access only to vendors.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'VENDOR'

class IsUser(permissions.BasePermission):
    """
    Allows access only to regular users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'USER'

class IsOwner(permissions.BasePermission):
    """
    Object-level permission to allow owners of an object to edit it.
    Assumes the model instance has a 'user' or 'owner' attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class IsVendorOrStaffOrReadOnly(permissions.BasePermission):
    """
    Allows authenticated vendors and staff to write, while allowing all others read-only.
    """
    def has_permission(self, request, view):
        # Read-only access is allowed for all users (including anonymous).
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to vendors and staff.        
        return request.user and (request.user.is_staff or request.user.role == 'VENDOR')

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Staff can edit any product.
        if request.user.is_staff:
            return True
        # Vendors can only edit their own products.
        return obj.vendor == request.user

class IsStaffOrSuperAdmin(permissions.BasePermission):
    """
    Allows access only to staff or superusers.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)

class CanViewOrder(permissions.BasePermission):
    """
    Object-level permission for viewing orders.
    """
    def has_object_permission(self, request, view, obj):
        # Staff and superadmins can view any order.
        if request.user.is_staff or request.user.is_superuser:
            return True
        # Regular users can only view their own orders.
        if request.user.role == 'USER':
            return obj.user == request.user
        # Vendors can view orders containing their products.
        if request.user.role == 'VENDOR':
            # This logic assumes the Order model has a related 'items' field
            # and the Product model has a 'vendor' foreign key.
            for item in obj.items.all():
                if item.product.vendor == request.user:
                    return True
        return False