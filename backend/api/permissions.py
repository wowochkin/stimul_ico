from rest_framework import permissions

from stimuli.models import StimulusRequest


class IsRequestOwnerOrAdmin(permissions.BasePermission):
    """Allow admins full access and limit regular users to their own requests."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff or request.user.has_perm('stimuli.view_all_requests'):
            return True

        if request.method in permissions.SAFE_METHODS:
            return obj.requested_by_id == request.user.id

        if obj.requested_by_id != request.user.id:
            return False

        if request.method in {'DELETE', 'PUT', 'PATCH'} and obj.status != StimulusRequest.Status.PENDING:
            return False

        return True
