from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to allow only owners of an object (Address) OR staff users.
    This should be used on viewsets where user-specific objects are returned.
    """
    def has_permission(self, request, view):
        # Must be authenticated for any non-read actions (you can tweak to allow read-only to anon)
        # Read-only access is allowed for all users (including anonymous).
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only allow authenticated users for write actions
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff users can do anything
        if request.user and request.user.is_staff:
            return True
        
        # Owners can view, edit, or delete their own objects
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        
        return getattr(obj, "user", None) == request.user
        