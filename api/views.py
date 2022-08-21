from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response

from api.serializers import *


########################
#         KFET         #
########################

# authentification nécessaire pour tous les appels de l'API KFET

# GET : récupère les informations de l'utilisateur actuel
class CurrentUserViewSet(viewsets.ModelViewSet):
    serializer_class = ConsommateurSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions,)
    queryset = Consommateur.objects.none()

    def list(self, request):
        try:
            consommateur = Consommateur.objects.get(consommateur=self.request.user.pk, activated=True)
        except Consommateur.DoesNotExist:
            return Response({'Consommateur does not exist'}, status=404)  # TODO: 404?
        serializer = self.get_serializer(consommateur)
        return Response(serializer.data)

# GET : récupérer tous les produits


class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions,)


# GET : récupérer tous les consommateurs
class ConsommateurViewSet(viewsets.ModelViewSet):
    queryset = Consommateur.objects.filter(activated=True)
    serializer_class = ConsommateurSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions,)


# GET : récupérer toutes les recharges pour tous les utilisateurs ou pour un en particulier
# POST : créer une recharge. Seuls les utilisateurs ayant été déclaré avec le droit appkfet|recharge|can add recharge
#        peuvent effectuer cette action
class RechargeViewSet(viewsets.ModelViewSet):
    serializer_class = RechargeSerializer
    http_method_names = ["get", "post", "options"]
    permission_classes = (permissions.DjangoModelPermissions,)
    lookup_field = "cible_recharge"

    def get_queryset(self, *args, **kwargs):
        if "cible_recharge" in self.kwargs:
            user_id = self.kwargs["cible_recharge"]
            consommateur = Consommateur.objects.filter(consommateur=user_id)
            if consommateur.count() == 1:
                queryset = Recharge.objects.filter(cible_recharge=consommateur[0])
            else:
                queryset = Recharge.objects.none()
        else:
            queryset = Recharge.objects.all()
        return queryset

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(data=serializer.data)


# GET : récupérer toutes les bucquages pour un utilisateur donné ou pour tous
# POST : créer un bucquage. Seuls les utilisateurs ayant été déclaré dans le groupe du produit à bucquer peuvent
#        effectuer cette action. Le groupe d'entité est préalablement doté du droit appkfet|bucquage|can add bucquage
class BucquageViewSet(viewsets.ModelViewSet):
    serializer_class = BucquageSerializer
    http_method_names = ["get", "post", "options"]
    lookup_field = "cible_bucquage"
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_queryset(self, *args, **kwargs):
        if "cible_bucquage" in self.kwargs:
            user_id = self.kwargs["cible_bucquage"]
            consommateur = Consommateur.objects.filter(pk=user_id)
            if consommateur.count() == 1:
                queryset = Bucquage.objects.filter(cible_bucquage=consommateur[0])
            else:
                queryset = Bucquage.objects.none()
        else:
            queryset = Bucquage.objects.all()
        return queryset

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(data=serializer.data)


# récupérer l'historique pour un utilisateur donné ou pour tous
class HistoryViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = HistorySerializer
    lookup_field = "cible_evenement"

    def get_queryset(self):
        if "cible_evenement" in self.kwargs:
            user_id = self.kwargs["cible_evenement"]
            consommateur = Consommateur.objects.filter(pk=user_id)
            if consommateur.count() == 1:
                queryset = History.objects.filter(
                    cible_evenement=consommateur[0]
                ).order_by("-date_evenement")
            else:
                queryset = History.objects.none()
        else:
            queryset = History.objects.all().order_by("-date_evenement")
        return queryset

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(data=serializer.data)

#########################
#         LYDIA         #
#########################


class RechargeLydiaViewSet(viewsets.ModelViewSet):
    serializer_class = RechargeLydiaSerializer
    http_method_names = ["get", "post", "options"]
    permission_classes = (permissions.DjangoModelPermissions,)
    lookup_field = "cible_recharge"

    def get_queryset(self, *args, **kwargs):
        if "cible_recharge" in self.kwargs:
            user_id = self.kwargs["cible_recharge"]
            consommateur = Consommateur.objects.filter(consommateur=user_id)
            if consommateur.count() == 1:
                queryset = RechargeLydia.objects.filter(cible_recharge=consommateur[0])
            else:
                queryset = RechargeLydia.objects.none()
        else:
            queryset = RechargeLydia.objects.all()
        return queryset

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(data=serializer.data)
