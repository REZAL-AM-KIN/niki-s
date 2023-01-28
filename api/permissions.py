from rest_framework import permissions
from appkfet.models import Pianss, Consommateur
from appuser.models import Utilisateur


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _is_ip_authorized(request):
    """
    if request.user.has_perm("appkfet.bypass_ip_constraint"):
        return True

    client_ip = get_client_ip(request)
    allowedIP = AuthorizedIP.objects.filter(ip=client_ip)
    # if the ip the user uses is in one of the user's groups
    # an ip can be listed more than one time
    for ip in allowedIP:
        if request.user.groups.filter(name=ip.groupe).exists():
            return True
    """
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

    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True

        if request.method == "GET":
            if user.has_perm("appevents.view_event"):
                return True
        if request.method == "POST":
            if user.has_perm("appevents.add_event"):
                return True

        if request.method in self.edit_methods:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        user = Utilisateur.objects.get(pk=request.user.pk)
        if user.is_superuser:
            return True

        if request.method == "GET":
            if user.has_perm("appevents.view_event"):
                return True

        if request.method in self.edit_methods:           # On s'occupe ici des permissions de modification uniquement
            if user.has_perm("appevents.change_event"):
                return True

            if user.has_perm("appevents.event_super_manager"):  #Si l'user à la perm d'admin des fin'ss alors on laisse éditer
                return True

            consommateur = Consommateur.objects.get(consommateur=user)
            return consommateur in obj.managers.all()  #On vérifie que l'utilisateur est dans la liste des managers
        return False


# Classe de permissions à combiner avec DjangoModelPermissions --> Autorise la modification des Events pour les managers
class EditProductEventPermission(permissions.BasePermission):
    edit_methods = ("PUT", "PATCH", "DELETE")

    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser:
            return True

        if request.method == "GET":
            if user.has_perm("appevents.view_productevent"):
                return True

        if request.method == "POST":
            if user.has_perm("appevents.add_productevent"):
                return True

        if request.method in self.edit_methods: # On return True si c'est une permissions d'édition (donc de détail) car on s'en occupe au niveau objet
            return True
        return False

    def has_object_permission(self, request, view, obj):
        user = Utilisateur.objects.get(pk=request.user.pk)
        if user.is_superuser:
            return True

        if request.method == "GET":
            if user.has_perm("appevents.view_productevent"):
                return True

        if request.method in self.edit_methods:           # On s'occupe ici des permissions de modification uniquement
            if user.has_perm("appevents.change_productevent"):
                return True

            if user.has_perm("appevents.event_super_manager"):  #Si l'user à la perm d'admin des fin'ss alors on laisse éditer
                return True

            consommateur = Consommateur.objects.get(consommateur=user)
            return consommateur in obj.parent_event.managers.all()  #On vérifie que l'utilisateur est dans la liste des managers

        return False


class BucquageEventPermission(permissions.BasePermission):
    detail_action = ("retrieve", "update", "partial_update", "destroy")

    def has_permission(self, request, view):
        user = request.user
        if user.is_superuser or user.has_perm("appevents.event_super_manager"):
            return True

        # Les permissions pour list sont dans la gestion du queryset
        if view.action == "list":
            return True

        # Les permissions pour create sont dans l'action create du viewset
        # (car necessite l'accès aux données du serializer)
        if view.action == "create":
            return True

        if view.action == "debucquage":
            if user.has_perm("appevents.event_super_manager"):  #Si l'user à la perm d'admin des fin'ss alors on laisse débucquer
                return True

        #Tout le monde peut acceder à ses bucquages
        if view.action == "my_bucquages":
            return True

        # Pour les actions de détail, les perms sont gérées dans has_object_permissions
        if view.action in self.detail_action:
            return True

        return False


    def has_object_permission(self, request, view, obj):
        user = Utilisateur.objects.get(pk=request.user.pk)
        if user.is_superuser or user.has_perm("appevents.event_super_manager"):
            return True

        if view.action == "debucquer":
            return False

        if view.action in self.detail_action:
            requester_consommateur = Consommateur.objects.get(consommateur=user)
            if requester_consommateur == obj.cible_participation:
                return True

            if requester_consommateur in obj.product_participation.parent_event.managers.all():
                return True

        return False
