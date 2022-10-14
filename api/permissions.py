from rest_framework import permissions
from appkfet.models import AuthorizedIP
from appuser.models import Utilisateur


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def _is_ip_authorized(request):
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


class AllowedIP(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return _is_ip_authorized(request)


class AllowedIPEvenSaveMethods(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_ip_authorized(request)


#Classe de permissions à combiner avec DjangoModelPermissions --> Autorise la modification des Events pour les managers
class EditEventPermission(permissions.BasePermission):
    edit_methods = ("PUT", "PATCH")

    def has_object_permission(self, request, view, obj):
        if request.method in self.edit_methods:           # On s'occupe ici des permissions de modification uniquement
            user = Utilisateur.objects.get(pk=request.user.pk)
            if user.is_superuser:
                return True

            if user.has_perm("appevents.event_super_manager"):  #Si l'user à la perm d'admin des fin'ss alors on laisse éditer
                return True

            return user in obj.managers.all()  #On vérifie que l'utilisateur est dans la liste des managers
        return False
