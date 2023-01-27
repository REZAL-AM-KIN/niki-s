from django.db.models import Q
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from api.serializers import *

from api.permissions import AllowedIP, AllowedIPEvenSaveMethods, get_client_ip, EditEventPermission, \
    EditProductEventPermission, BucquageEventPermission


########################
#         KFET         #
########################

# authentification nécessaire pour tous les appels de l'API KFET

# GET : recupère les permissions de l'utilisateur


class PermissionsViewSet(viewsets.ModelViewSet):
    serializer_class = PermissionsSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions, AllowedIPEvenSaveMethods,)
    queryset = Utilisateur.objects.none()

    def list(self, request):
        user = Utilisateur.objects.get(pk=request.user.pk)
        data = {}
        data["all"] = user.is_superuser
        data["ipIdentification"] = []
        ips = AuthorizedIP.objects.filter(ip=get_client_ip(request))
        for ip in ips:
            data["ipIdentification"].append(ip.groupe)
        data["groupes"] = user.groups.all()
        data["recharge"] = user.has_perm("appkfet.add_recharge")
        serializer = self.get_serializer(data)
        return Response(serializer.data)


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
    permission_classes = (permissions.DjangoModelPermissions, AllowedIP,)
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

    def create(self, request, *arg, **kwargs):
        # here we get the Utilisateur origin of the request
        utilisateur = Utilisateur.objects.get(pk=request.user.pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(initiateur_evenement=utilisateur)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# GET : récupérer toutes les bucquages pour un utilisateur donné ou pour tous
# POST : créer un bucquage. Seuls les utilisateurs ayant été déclaré dans le groupe du produit à bucquer peuvent
#        effectuer cette action. Le groupe d'entité est préalablement doté du droit appkfet|bucquage|can add bucquage


class BucquageViewSet(viewsets.ModelViewSet):
    serializer_class = BucquageSerializer
    http_method_names = ["get", "post", "options"]
    lookup_field = "cible_bucquage"
    permission_classes = (permissions.DjangoModelPermissions, AllowedIP,)

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

    def create(self, request, *arg, **kwargs):
        # here we get the Utilisateur origin of the request
        utilisateur = Utilisateur.objects.get(pk=request.user.pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(initiateur_evenement=utilisateur)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
    permission_classes = (permissions.DjangoModelPermissions, AllowedIP,)
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


#########################
#        FIN'SS         #
#########################


# GET : récupère la liste et les informations des tous les fin'ss dont l'utilisateur est gestionnaire.
# POST : Ajoute un evenement (sous permissions addEvent)
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = (EditEventPermission,)  #On combine les permissions de bases et la perm custom pour overide uniquement les permissions de modification d'objet
    http_method_names = ["get", "options", "post", "patch", "put", "delete"]

    def get_queryset(self):
        user = Utilisateur.objects.get(pk=self.request.user.pk)
        if user.has_perm("appevents.event_super_manager") or user.is_superuser:
            return Event.objects.all()

        return Event.objects.filter(ended=False) # Si c'est un utilisateur Lambda, il ne peut voir que les Event non cloturé


# GET : renvoi tous les produits dont l'utilisateur peut gérer le fin'ss.
# Filter : finss=<id finss> --> renvoi les produits du finss passer en argument url
class ProductEventViewSet(viewsets.ModelViewSet):
    serializer_class = ProductEventSerializer
    permission_classes = (EditProductEventPermission,) # On combine les permissions de bases et la perm custom pour overide uniquement les permissions de modification d'objet
    http_method_names = ["get", "options", "post", "patch", "put", "delete"]
    queryset = ProductEvent.objects.all()


    def get_queryset(self):
        finss_id = self.request.query_params.get("finss", None)

        #Retrieving complete queryset
        if self.request.user.has_perm("appevents.event_super_manager") or self.request.user.is_superuser:
            self.queryset = self.queryset
        else:
            self.queryset = self.queryset.filter(parent_event__ended=False)

        if finss_id is None:
            return self.queryset
        if not finss_id.isdigit():
            return self.queryset.none()
        return self.queryset.filter(parent_event__pk=finss_id)



# GET : renvoi toutes les participations classées par Consommateur :
#                                  [{consommateur_id:id, participation:[liste des participations de l'utilisateur}, ...]
# Filter : finss=<id finss> --> filtre les participations qui ne concernent que le finss id finss
class BucqageEventViewSet(viewsets.ModelViewSet):
    permission_classes = (BucquageEventPermission,)

    def get_serializer_class(self):
        if self.action == "list":
            return BucquageEventSerializer
        if self.action in ["debucquer", "debucquage"]:
            return DebucquageEventSerializer

        return ParticipationEventSerializer

    # Si l'action est list alors il faut que l'on retourne un queryset de Consommateur
    # (car serializer BucquageEventSerializer basé sur Consomateur)
    # Sinon on retourne l'ensemble des Participations.
    def get_queryset(self):
        if self.action == "list":
            consommateur = Consommateur.objects.get(consommateur=self.request.user)
            # Si superuser ou supermanagers on sélectionne tous les consommateurs qui ont des participations
            # sur un fin'ss en cours
            if self.request.user.has_perm("appevents.event_super_manager") \
                    or self.request.user.is_superuser:
                obj = Consommateur.objects.filter(
                    participation_event__product_participation__parent_event__ended=False
                    ).distinct()
                return obj

            # Si utilisateur manager d'un fin'ss, on récupère tous les Consommateurs qui ont des participations
            # sur un fin'ss en cours managé par l'utilisateur
            if Event.objects.filter(managers=consommateur).count() != 0:
                return Consommateur.objects.filter(
                    Q(participation_event__product_participation__parent_event__ended=False) &
                    Q(participation_event__product_participation__parent_event__managers=consommateur)
                )

        # Si c'est une autre action que list alors on renvoie la liste de toutes les participations de fin'ss actif
        return ParticipationEvent.objects.filter(product_participation__parent_event__ended=False)

    # On permet la création de plusieurs objets en une seule fois
    # et l'édition d'un objet via le post (car perform_create appelle la méthode save du serializer)
    def create(self, request, *args, **kwargs):
        success = []
        errors = []
        for data in request.data:
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                if not self.request.user.has_perm("appevents.event_super_manager") \
                        and not self.request.user.is_superuser:
                    if serializer.validated_data.get("cible_participation") \
                            != Consommateur.objects.get(consommateur=request.user):
                        errors.append(["You don't have permission to access participations "
                                       "of Consommateur "+str(serializer.data.get("cible_participation"))])
                        continue

                self.perform_create(serializer)  # On appel le create du serializer (ce dernier est modifier pour permettre l'update des items)
                success.append(serializer.data)
            else:
                errors.append(serializer.errors)

        if len(errors) == 0:
            return Response(success, status=status.HTTP_200_OK)
        else:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def debucquer(self, request, pk=None):
        user = Utilisateur.objects.get(pk=request.user.pk)
        try:
            participation = ParticipationEvent.objects.get(pk=pk)
        except ParticipationEvent.DoesNotExist:
            return Response({"Cannot resolve participation"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DebucquageEventSerializer(data=request.data)

        if serializer.is_valid():
            debucquage = participation.debucquage(user, serializer.validated_data.get("negatss"))
            if debucquage is True:
                return Response({'status': 'Participation débucquée'}, status=status.HTTP_200_OK)
            else:
                return Response({debucquage}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # TODO : Delete ou pas de création si quantité = 0
    ### /bucquage/ ###
    # POST : Prends une liste de Debucquage format: [{id_participation:<id>, (optionel) negats:<True|False>}, ... ]
    @action(methods=['POST'], detail=False)
    def debucquage(self, request):
        user = Utilisateur.objects.get(pk=request.user.pk)
        success = []
        errors = []

        serializer = DebucquageEventSerializer(data=request.data, many=True)

        if serializer.is_valid():
            for p in serializer.validated_data:
                participation_id = p.get("participation_id")
                if participation_id == -1:
                    return Response({"All participation_id must be specified"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    participation = ParticipationEvent.objects.get(pk=participation_id)
                except ParticipationEvent.DoesNotExist:
                    errors.append({
                        "participation_id": participation_id,
                        "error": "Cannot resolve participation"
                    })
                    continue


                debucquage = participation.debucquage(user, p.get("negatss"))
                if debucquage is True:
                    success.append({
                        "participation_id": participation_id,
                        "status": "Participation débucquée"
                    })
                else:
                    errors.append({
                        "participation_id": participation_id,
                        "error": debucquage
                    })

            return Response({"success": success, "errors": errors})

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # GET : Affiche la liste
    @debucquage.mapping.get
    def debucquage_list(self, request):
        queryset = ParticipationEvent.objects.filter(
            Q(participation_debucquee=True)
            & Q(product_participation__parent_event__ended=False)
        )
        serializer = ParticipationEventSerializer(instance=queryset, many=True)
        return Response(serializer.data)

    # Affiche la liste des participations de l'utilisateur connecté
    @action(methods=['GET'], detail=False)
    def my_bucquages(self, request):
        consommateur = Consommateur.objects.get(consommateur=request.user)

        myparticipations = ParticipationEvent.objects.filter(
            Q(cible_participation=consommateur)
            & Q(product_participation__parent_event__ended=False)
        )

        finss_id = request.query_params.get("finss", None)

        # Si un finss_id est donné, alors on filtre les Participations
        if finss_id is not None:
            if finss_id.isdigit():
                myparticipations = myparticipations.filter(product_participation__parent_event__pk=finss_id)

        serializer = ParticipationEventSerializer(instance=myparticipations, many=True)
        return Response(serializer.data)
