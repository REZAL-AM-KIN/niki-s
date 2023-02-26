from rest_framework import permissions
from appkfet.models import Pianss



class AllowedPianss(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.has_perm("appkfet.bypass_pianss_constraint"):
            return True

        pianss_token = request.pianss_token
        if pianss_token is None:
            return False

        return Pianss.objects.filter(token=pianss_token).exists()


