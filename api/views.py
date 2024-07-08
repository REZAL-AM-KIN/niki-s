from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from api.serializers import *

from api.permissions import AllowedIP, AllowedIPEvenSaveMethods, get_client_ip, EditEventPermission, \
    EditProductEventPermission, BucquageEventPermission, RequiersConsommateur

from django.http.request import QueryDict


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
        data["entities"] = user.entities.all()
        data["recharge"] = user.has_perm("appkfet.add_recharge")
        serializer = self.get_serializer(data)
        return Response(serializer.data)


# GET : récupère les informations de l'utilisateur actuel
class CurrentUserViewSet(viewsets.ModelViewSet):
    serializer_class = ConsommateurSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)
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
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)


# GET : recuperer les groupes (catégories)
class EntiteViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntiteSerializer
    http_method_names = ["get", "options", "post", "put", "delete"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)


# GET : récupérer tous les consommateurs
class ConsommateurViewSet(viewsets.ModelViewSet):
    queryset = Consommateur.objects.filter(activated=True)
    serializer_class = ConsommateurSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)


# GET : récupérer toutes les recharges pour tous les utilisateurs ou pour un en particulier
# POST : créer une recharge. Seuls les utilisateurs ayant été déclaré avec le droit appkfet|recharge|can add recharge
#        peuvent effectuer cette action
class RechargeViewSet(viewsets.ModelViewSet):
    serializer_class = RechargeSerializer
    http_method_names = ["get", "post", "options"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur, AllowedIP,)
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
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur, AllowedIP,)

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
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)
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
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur, AllowedIP,)
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
    permission_classes = (RequiersConsommateur, EditEventPermission,)  #On combine les permissions de bases et la perm custom pour overide uniquement les permissions de modification d'objet
    http_method_names = ["get", "options", "post", "patch", "put", "delete"]

    def get_serializer_class(self):
        if "fermeture_prebucquage" in self.action:
            return FermeturePrebucquageEventSerializer
        return EventSerializer

    def get_queryset(self):
        user = Utilisateur.objects.get(pk=self.request.user.pk)
        if user.has_perm("appevents.event_super_manager") or user.is_superuser:
            return Event.objects.all()

        return Event.objects.filter(~Q(etat_event=Event.EtatEventChoices.TERMINE)) # Si c'est un utilisateur Lambda, il ne peut voir que les Event non cloturé



    @action(methods=['POST'], detail=False)
    def fermeture_prebucquage(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = Event.objects.get(pk=serializer.validated_data["id"])
        serializer.fermeture_prebucquage(serializer.validated_data)
        headers = self.get_success_headers(serializer.data)
        return Response({'status': 'Prébucquage fermé pour "'+event.titre+'"'}, status=status.HTTP_200_OK, headers=headers)


    # GET : Affiche la liste
    @fermeture_prebucquage.mapping.get
    def fermeture_prebucquage_list(self, request):
        user = Utilisateur.objects.get(pk=request.user.pk)
        if user.has_perm("appevents.event_super_manager") or user.is_superuser:
            queryset = Event.objects.filter(etat_event=Event.EtatEventChoices.PREBUCQUAGE)
        else:
            consommateur = Consommateur.objects.get(consommateur=request.user)
            queryset = Event.objects.filter(
                Q(etat_event=Event.EtatEventChoices.PREBUCQUAGE)
                & Q(managers=consommateur)
            )
        serializer = self.get_serializer(instance=queryset, many=True)
        return Response(serializer.data)



# GET : renvoi tous les produits dont l'utilisateur peut gérer le fin'ss.
# Filter : finss=<id finss> --> renvoi les produits du finss passer en argument url
class ProductEventViewSet(viewsets.ModelViewSet):
    serializer_class = ProductEventSerializer
    permission_classes = (RequiersConsommateur, EditProductEventPermission,) # On combine les permissions de bases et la perm custom pour overide uniquement les permissions de modification d'objet
    http_method_names = ["get", "options", "post", "patch", "put", "delete"]
    queryset = ProductEvent.objects.all()


    def get_queryset(self):
        finss_id = self.request.query_params.get("finss", None)

        #Retrieving complete queryset
        if self.request.user.has_perm("appevents.event_super_manager") or self.request.user.is_superuser:
            self.queryset = self.queryset
        else:
            self.queryset = self.queryset.filter(~Q(parent_event__etat_event=Event.EtatEventChoices.TERMINE))

        if finss_id is None:
            return self.queryset
        if not finss_id.isdigit():
            return self.queryset.none()
        return self.queryset.filter(parent_event__pk=finss_id)



# GET : renvoi toutes les participations classées par Consommateur :
#                                  [{consommateur_id:id, participation:[liste des participations de l'utilisateur}, ...]
# Filter : finss=<id finss> --> filtre les participations qui ne concernent que le finss id finss
class BucqageEventViewSet(viewsets.ModelViewSet):
    permission_classes = (RequiersConsommateur, BucquageEventPermission,)

    def get_serializer_class(self):
        if self.action == "list":
            return BucquageEventSerializer
        if self.action == "debucquage":
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
                    participation_event__product_participation__parent_event__etat_event__lt=Event.EtatEventChoices.TERMINE
                    ).distinct()
                return obj

            # Si utilisateur manager d'un fin'ss, on récupère tous les Consommateurs qui ont des participations
            # sur un fin'ss en cours managé par l'utilisateur
            if Event.objects.filter(managers=consommateur).count() != 0:
                return Consommateur.objects.filter(
                    Q(participation_event__product_participation__parent_event__etat_event__lt=Event.EtatEventChoices.TERMINE) &
                    Q(participation_event__product_participation__parent_event__managers=consommateur)
                ).distinct()
            return Consommateur.objects.none()

        # Si c'est une autre action que list alors on renvoie la liste de toutes les participations de fin'ss actif
        return ParticipationEvent.objects.filter(product_participation__parent_event__etat_event__lt=Event.EtatEventChoices.TERMINE)

    # On permet la création de plusieurs objets en une seule fois
    # et l'édition d'un objet via le post (car perform_create appelle la méthode save du serializer)
    def create(self, request, *args, **kwargs):
        success = []
        errors = []
        if type(request.data) is QueryDict or type(request.data) is dict:
            datas = [request.data]
        else:
            datas = request.data
        for data in datas:
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

    # TODO : Delete ou pas de création si quantité = 0
    ### /bucquage/ ###
    # POST : Prends une liste de Debucquage format: [{id_participation:<id>, (optionel) negats:<True|False>}, ... ] ou
    # simplement {id_participation:<id>, (optionel) negats:<True|False>}
    @action(methods=['POST'], detail=False)
    def debucquage(self, request):
        user = Utilisateur.objects.get(pk=request.user.pk)

        success = []
        errors = []

        if type(request.data) is QueryDict or type(request.data) is dict:
            datas = [request.data]
        else:
            datas = request.data

        serializer = DebucquageEventSerializer(data=datas, many=True, context={'request': request})

        if serializer.is_valid():
            def message_debucquage_valide(participation_id):
                return {"participation_id": participation_id, "status": "Participation débucquée"}
            def message_debucquage_non_valide(participation_id, error):
                return {"participation_id": participation_id, "error": error}

            # on traite les participations à débucquer par consommateur
            participations_request = {p_data.get("participation_id"): p_data.get("negatss") for p_data in serializer.validated_data}
            participations = ParticipationEvent.objects.filter(pk__in=participations_request.keys())
            consommateurs = {p.cible_participation for p in participations}
            for consommateur in consommateurs:
                # on sépare les participations qu'on autorise à débucquer en négatif des autres
                participations_filter = participations.filter(cible_participation=consommateur)
                participations_non_negats = participations_filter.filter(pk__in=[p.pk for p in participations_filter if not participations_request[p.pk]])
                participations_negats = participations_filter.filter(pk__in=[p.pk for p in participations_filter if participations_request[p.pk]])

                # pour les participations qui ne seront pas débucqués en négatif, on regarde si ensemble, elles font passer le consommateur en négatif
                cout_non_negats = sum([participation.prix_total for participation in participations_non_negats])
                if consommateur.testdebit(cout_non_negats):
                    for participation in participations_non_negats:
                        debucquage = participation.debucquage(user, False)
                        if debucquage is True:
                            success.append(message_debucquage_valide(participation.id))
                        else:
                            errors.append(message_debucquage_non_valide(participation.id, debucquage))
                else:
                    errors.extend([message_debucquage_non_valide(p.pk, "Le consommateur n'a pas assez d'argent") for p in participations_non_negats])

                # on débucque ensuite les participations du consommateur qu'on autorise à être débucquée en négatif.
                for participation in participations_negats:
                    debucquage = participation.debucquage(user, True)
                    if debucquage is True:
                        success.append(message_debucquage_valide(participation.id))
                    else:
                        errors.append(message_debucquage_non_valide(participation.id, debucquage))

            if len(errors) > 0:
                resp_status = status.HTTP_400_BAD_REQUEST
            else:
                resp_status = status.HTTP_200_OK
            return Response({"success_count": len(success), "errors_count": len(errors), "success": success,
                             "errors": errors}, status=resp_status)

        else:
            errors=[]
            for index in range(len(serializer.data)):
                err = serializer.errors[index]
                if err != {}:
                    errors.append({"participation_id": serializer.data[index].get("participation_id"),
                                    "status": err})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # GET : Affiche la liste
    @debucquage.mapping.get
    def debucquage_list(self, request):
        queryset = ParticipationEvent.objects.filter(
            Q(product_participation__parent_event__etat_event=Event.EtatEventChoices.DEBUCQUAGE)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # Affiche la liste des participations de l'utilisateur connecté
    @action(methods=['GET'], detail=False)
    def my_bucquages(self, request):
        consommateur = Consommateur.objects.get(consommateur=request.user)

        myparticipations = ParticipationEvent.objects.filter(
            Q(cible_participation=consommateur)
            & Q(product_participation__parent_event__etat_event__lt=Event.EtatEventChoices.TERMINE)
        )

        finss_id = request.query_params.get("finss", None)

        # Si un finss_id est donné, alors on filtre les Participations
        if finss_id is not None:
            if finss_id.isdigit():
                myparticipations = myparticipations.filter(product_participation__parent_event__pk=finss_id)

        serializer = self.get_serializer(myparticipations, many=True)
        return Response(serializer.data)
