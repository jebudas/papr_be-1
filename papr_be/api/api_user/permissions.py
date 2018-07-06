from rest_framework import permissions

class UpdateOwnProfile(permissions.BasePermission):

    """ allow users to update profile """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.id == request.user.id:
            return True
        else:
            return False


class PostOwnStatus(permissions.BasePermission):

    """ allow users to update their own status """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.user_profile.id == request.user.id:
            return True
        else:
            return False
