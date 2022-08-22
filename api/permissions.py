from rest_framework import permissions
from appkfet.models import AuthorizedIP


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AllowedIP(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.has_perm("appkfet.bypass_ip_constraint"):
            return True

        client_ip = get_client_ip(request)
        allowedIP = AuthorizedIP.objects.filter(ip=client_ip)
        # if the ip the user uses is in one of the user's groups
        # an ip can be listed more than one time
        for ip in allowedIP:
            if request.user.groups.filter(name=ip.groupe).exists():
                return True

        return False


class AllowedIPEvenSaveMethods(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.has_perm("appkfet.bypass_ip_constraint"):
            return True

        client_ip = get_client_ip(request)

        allowedIP = AuthorizedIP.objects.filter(ip=client_ip)
        # if the ip the user uses is in one of the user's groups
        # an ip can be listed more than one time
        for ip in allowedIP:
            if request.user.groups.filter(name=ip.groupe).exists():
                return True

        return False
