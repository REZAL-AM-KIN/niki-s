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

        # Check if the user is connect with a pianss
        if not hasattr(request, "pianss_token"):
            return False

        return Pianss.objects.filter(token=request.pianss_token).exists()


# Permission pour l'accès a l'endpoint pian'ss
class PianssPermission(permissions.DjangoModelPermissions):
    def has_permission(self, request, view):
        if request.method == "GET":
            if request.user.has_perm("appkfet.view_pianss"):
                return True
            return False
        return super().has_permission(request, view)


