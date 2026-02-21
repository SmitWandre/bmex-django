"""
Custom permissions for BMEX Masses API

Read-only API - all endpoints are GET only.
"""

from rest_framework import permissions


class ReadOnly(permissions.BasePermission):
    """
    Global read-only permission.
    Only safe methods (GET, HEAD, OPTIONS) are allowed.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
