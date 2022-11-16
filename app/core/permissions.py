from rest_framework.permissions import BasePermission, IsAuthenticated  # noqa


class DoesUserHaveTier(BasePermission):
    """
    Object-level permission to only allow users with tier.
    """

    message = "User does not have tier."

    def has_permission(self, request, view):
        return request.user.tier


class CanUserCreateLink(BasePermission):
    """
    Object-level permission to only allow users who can create binary link..
    """

    message = "User does not have permissions to create link."

    def has_permission(self, request, view):
        return request.user.tier.can_create_link
