from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters
from datetime import timedelta
from django.utils import timezone

from api.serializers import *

from api.permissions import AllowedIP, AllowedIPEvenSaveMethods, get_client_ip, EditEventPermission, \
    EditProductEventPermission, BucquageEventPermission, RequiersConsommateur, ProduitPermission

from django.http.request import QueryDict
from django.db.models.functions import Lower

########################
#         KFET         #
########################


class CaseInsensitiveOrderingFilter(filters.OrderingFilter):
    """Permet de trier les résultats de la requête en ignorant la casse des champs définit dans ordering_case_insensitive_fields,
    et d'avoir des alias pour les champs de tri dans replace_ordering_fields.
    replace_ordering_fields est 'appliqué' en premier, puis ordering_case_insensitive_fields"""
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        insensitive_ordering = getattr(view, 'ordering_case_insensitive_fields', ())
        if ordering:
            new_ordering = []
            for field in ordering:
                if (field[1:] if field.startswith('-') else field) in insensitive_ordering:
                    new_ordering.append(Lower(field[1:]).desc() if field.startswith('-') else Lower(field).asc())
                else:
                    new_ordering.append(field)
            return queryset.order_by(*new_ordering)

        return queryset

    def get_ordering(self, request, queryset, view):
        ordering = super(CaseInsensitiveOrderingFilter, self).get_ordering(request, queryset, view)
        fields_to_replace = getattr(view, 'replace_ordering_fields', None)
        if fields_to_replace and ordering:
            new_ordering = []
            for ordering_field in ordering:
                reverse = ordering_field.startswith('-')
                field = ordering_field[1:] if reverse else ordering_field
                if fields_to_replace.get(field):
                    new_ordering.append(("-" if reverse else "")+fields_to_replace[field])
                else:
                    new_ordering.append(ordering_field)
            return new_ordering
        return ordering


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
        data["entities_manageable"] = user.entities_manageable.all()
        data["recharge"] = user.has_perm("appkfet.add_recharge")
        data["event_debucquage_negats"] = user.has_perm("appevent.event_debucquage_negats")
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
    http_method_names = ["get", "options", "post", "put", "delete"]
    permission_classes = (ProduitPermission, RequiersConsommateur)
    serializer_class = ProduitSerializer


# récupérer les produits qui appartiennent à une entité d'id donnée
class ProduitByEntityViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)
    serializer_class = ProduitSerializer
    lookup_field = "cible_entity"
    filter_backends = [filters.SearchFilter, CaseInsensitiveOrderingFilter]
    ordering_fields = ["nom", "prix", "raccourci", "stock"]
    ordering_case_insensitive_fields = ["nom", "raccourci"]
    search_fields = ["raccourci", "nom"]

    def get_queryset(self):
        if "cible_entity" in self.kwargs or "cible_entity" in self.request.query_params:
            entite_id = self.request.query_params.get("cible_entity", None)
            if entite_id is None:
                entite_id = self.kwargs["cible_entity"]
            if not entite_id.isdigit():
                queryset = Produit.objects.none()
            else:
                entite = Entity.objects.filter(pk=entite_id)
                if entite.count() == 1:
                    queryset = Produit.objects.filter(
                        entite=entite[0]
                    )
                else:
                    queryset = Produit.objects.none()
        else:
            queryset = Produit.objects.all()
        return queryset

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(data=serializer.data)


# GET : recuperer les groupes (catégories)
class EntiteViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntiteSerializer
    http_method_names = ["get", "options", "post", "put", "delete"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)


# GET : recuperer les entités que l'utilisateur peut débucquer/gérer
class MesEntitesViewSet(viewsets.ModelViewSet):
    serializer_class = EntiteSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom"]

    def get_queryset(self):
        user = Utilisateur.objects.get(pk=self.request.user.pk)
        if user.has_perm("appkfet.produit_super_manager"):
            return Entity.objects.all().order_by(Lower("nom").asc())
        queryset = user.entities.all() | user.entities_manageable.all()
        return queryset.order_by(Lower("nom").asc())


# GET : recuperer les entités que l'utilisateur peut gérer
class MesEntitesManageablesViewSet(viewsets.ModelViewSet):
    serializer_class = EntiteSerializer
    http_method_names = ["get", "options"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom"]

    def get_queryset(self):
        user = Utilisateur.objects.get(pk=self.request.user.pk)
        return user.entities_manageable.all().order_by(Lower("nom").asc())


# GET : récupérer tous les consommateurs
class ConsommateurViewSet(viewsets.ModelViewSet):
    queryset = Consommateur.objects.filter(activated=True)
    serializer_class = ConsommateurSerializer
    http_method_names = ["get", "options", "patch"]
    permission_classes = (permissions.DjangoModelPermissions, RequiersConsommateur,)
    filter_backends = [filters.SearchFilter]
    search_fields = ["consommateur__first_name", "consommateur__last_name", "consommateur__bucque", "consommateur__fams", "consommateur__proms"]

    @action(methods=['PATCH'], detail=True)
    def annulerDernierDebucquage(self, request, pk=None):
        request_user = Utilisateur.objects.get(pk=request.user.pk)
        try:
            consommateur = Consommateur.objects.get(pk=pk)
        except Consommateur.DoesNotExist:
            return Response({"detail": "Consommateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        last_debucquage = consommateur.getDernierDebucquage()

        if last_debucquage is None:
            return Response({"detail": "Aucun débucquage pour ce consommateur"}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() - last_debucquage.date > timedelta(minutes=5):
            return Response({"detail": "Vous ne pouvez annuler un débucquage exécuté il y a plus de 5 minutes"},
                            status=status.HTTP_403_FORBIDDEN)

        # TODO? perm pour bypass
        if last_debucquage.initiateur_evenement != request_user:
            return Response({"detail": "Vous ne pouvez pas annuler un débucquage executé par un autre utilisateur"},
                            status=status.HTTP_403_FORBIDDEN)

        res, message = last_debucquage.annuler()
        if res:
            return Response({"detail": "Débucquage '" + str(message) + "' annulé"}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        return Response({"detail": "Create non autorisée"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
        if "cible_evenement" in self.kwargs or "cible_evenement" in self.request.query_params:
            user_id = self.request.query_params.get("cible_evenement", None)
            if user_id is None:
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
    filter_backends = [filters.SearchFilter, CaseInsensitiveOrderingFilter]
    ordering_fields = ["titre", "date_event"]
    ordering_case_insensitive_fields = ["titre"]
    search_fields = ["titre", "description", "date_event"]

    def get_serializer_class(self):
        if self.action in ["fermeture_prebucquage", "fermeture_bucquage", "fermeture_debucquage"]:
            # On n'a besoin d'aucune donnée dans champ data de la requête
            return serializers.BaseSerializer
        return EventSerializer

    def get_queryset(self):
        user = Utilisateur.objects.get(pk=self.request.user.pk)
        if user.has_perm("appevents.event_super_manager") or user.is_superuser:
            return Event.objects.all()

        return Event.objects.filter(~Q(etat_event=Event.EtatEventChoices.TERMINE)) # Si c'est un utilisateur Lambda, il ne peut voir que les Event non cloturé

    @action(methods=['PATCH'], detail=True)
    def fermeture_prebucquage(self, request, pk=None):
        event = self.get_object()
        if event.etat_event != Event.EtatEventChoices.PREBUCQUAGE:
            return Response({'status': 'L\'évènement "'+event.titre+'" n\'est pas en mode prébucquage'}, status=status.HTTP_400_BAD_REQUEST)
        event.mode_bucquage()
        return Response({'status': 'Prébucquage fermé pour "'+event.titre+'"'}, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=True)
    def fermeture_bucquage(self, request, pk=None):
        event = self.get_object()
        if event.etat_event != Event.EtatEventChoices.BUCQUAGE:
            return Response({'status': 'L\'évènement "'+event.titre+'" n\'est pas en mode bucquage'}, status=status.HTTP_400_BAD_REQUEST)
        # TODO: vérifier si tout les prébucquages sont passés? (et rajouter un booléen dans les données de la requête pour forcer)
        event.mode_debucquage()
        return Response({'status': 'Bucquage fermé pour "'+event.titre+'"'}, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=True)
    def fermeture_debucquage(self, request, pk=None):
        event = self.get_object()
        if event.etat_event != Event.EtatEventChoices.DEBUCQUAGE:
            return Response({'status': 'L\'évènement "'+event.titre+'" n\'est pas en débucquage'}, status=status.HTTP_400_BAD_REQUEST)
        not_all_debucquees = event.productevent_set.all().filter(
            Q(participationevent__participation_debucquee=False) & Q(participationevent__participation_bucquee=True)
        ).exists()
        if not_all_debucquees:
            return Response({'status': 'Toutes les participations ne sont pas débucquées pour "' + event.titre + '"'},
                            status=status.HTTP_400_BAD_REQUEST)
        event.end()
        return Response({'status': 'Débucquage fermé pour "'+event.titre+'"'}, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True)
    def progression_bucquage(self, request, pk=None):
        event = self.get_object()
        prebucquees = Consommateur.objects.filter(
            participation_event__product_participation__parent_event=event,
            participation_event__prebucque_quantity__gt=0
        ).distinct()
        if event.etat_event < Event.EtatEventChoices.BUCQUAGE:
            nb_bucquees_et_prebucquees = 0
        else:
            # il faut quelqu'un relise ce calcul
            # j'essaye d'avoir seulement le nombre de consommateur prébucqué qui ont toutes leur participations bucquées
            nb_bucquees_et_prebucquees = prebucquees.filter(
                participation_event__product_participation__parent_event=event,
                participation_event__participation_bucquee=True,
                participation_event__prebucque_quantity__gt=0,
                participation_event__quantity__gt=0
            ).distinct().count() - prebucquees.filter(
                participation_event__product_participation__parent_event=event,
                participation_event__prebucque_quantity__gt=0,
                participation_event__quantity=0
            ).distinct().count()

        return Response({'prebucquees': prebucquees.count(), 'bucquees': nb_bucquees_et_prebucquees}, status=status.HTTP_200_OK)


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
#                                  [{ consommateur_id, nom, prenom, bucque, fams, proms, solde,
#                                     participation:[liste des participations de l'utilisateur
#                                   },
#                                   ...]
# Filter : finss=<id finss> --> filtre les participations qui ne concernent que le finss id finss
# On peut créer/éditer directement des produits en POST/PATCH/PUT
# Cet endpoint sert surtout pour "éditer" les participations d'un finss
# l'action /prebucquage/ permet de créer/éditer des prébucquages avec comme champs
#     {
#         "cible_participation": <id Consommateur>,
#         "product_participation": <id ProductEvent>,
#         "prebucque_quantity": <int>
#     }
# l'action /bucquage/ permet de créer/éditer des bucquages avec comme champs
#     {
#         "cible_participation": <id Consommateur>,
#         "product_participation": <id ProductEvent>,
#         "quantity": <int>
#     }
# l'action /debucquage/ permet de débucquer des participations avec comme champs
#     {
#         "id": <id ParticipationEvent>,
#         "negatss": <bool> - optionnal. si True, on peut débucquer en Négatif (si l'utilisateur a la permission appevents.event_debucquage_negats)
#     }
# ces 3 actions renvoie en GET une liste des participations qui peuvent être éditées par l'action

class BucqageEventViewSet(viewsets.ModelViewSet):
    permission_classes = (RequiersConsommateur, BucquageEventPermission,)
    http_method_names = ["get", "options", "post", "patch", "put"]

    def get_serializer_class(self):
        if self.action == "list":
            return BucquageEventDefaultSerializer
        if self.action == "debucquage" or self.action == "debucquage_list":
            return DebucquageEventSerializer
        if self.action == "bucquage" or self.action == "bucquage_list":
            return BucquageEventSerializer
        if self.action == "prebucquage" or self.action == "prebucquage_list":
            return PrebucquageEventSerializer

        return ParticipationEventSerializer

    # Si l'action est list alors il faut que l'on retourne un queryset de Consommateur
    # (car serializer BucquageEventSerializer basé sur Consomateur)
    # Sinon on retourne l'ensemble des Participations.
    def get_queryset(self):
        if self.action == "list":
            request_consommateur = Consommateur.objects.get(consommateur=self.request.user)

            finss_id = self.request.query_params.get("finss", None)
            consommateur_id = self.request.query_params.get("consommateur_id", None)
            # Si finss_id est spécifié, on récupère les Consommateurs qui ont des participations sur ce fin'ss,
            # indépendament de si le fin'ss est terminé ou non. Il faut cepandant que l'utilisateur puisse manager ce fin'ss.
            # Si finss_id n'est pas spécifié, consommateur_id n'est pas utilisé.
            if finss_id is not None and finss_id.isdigit():
                if (not (self.request.user.has_perm("appevents.event_super_manager") or self.request.user.is_superuser)
                        and request_consommateur not in Event.objects.get(pk=finss_id).managers.all()):
                    return Consommateur.objects.none()
                if consommateur_id is not None and consommateur_id.isdigit():
                    return Consommateur.objects.filter(
                        participation_event__product_participation__parent_event__pk=finss_id,
                        pk=consommateur_id
                    ).distinct()
                return Consommateur.objects.filter(
                    participation_event__product_participation__parent_event__pk=finss_id,
                ).distinct()

            # Si superuser ou supermanagers on sélectionne tous les consommateurs qui ont des participations
            # sur un fin'ss en cours
            if self.request.user.has_perm("appevents.event_super_manager") or self.request.user.is_superuser:
                obj = Consommateur.objects.filter(
                    participation_event__product_participation__parent_event__etat_event__lt=Event.EtatEventChoices.TERMINE
                    ).distinct()
                return obj

            # Si utilisateur manager d'un fin'ss, on récupère tous les Consommateurs qui ont des participations
            # sur un fin'ss en cours managé par l'utilisateur
            if Event.objects.filter(managers=request_consommateur).count() != 0:
                return Consommateur.objects.filter(
                    Q(participation_event__product_participation__parent_event__etat_event__lt=Event.EtatEventChoices.TERMINE) &
                    Q(participation_event__product_participation__parent_event__managers=request_consommateur)
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

    @action(methods=['POST'], detail=False)
    def prebucquage(self, request):
        success = []
        errors = []

        if type(request.data) is QueryDict or type(request.data) is dict:
            datas = [request.data]
        else:
            datas = request.data
        for data in datas:
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save()  # gère la création ou édition (ou supression si prebucque_quantity = 0) de la participation
                if serializer.validated_data.get("prebucque_quantity") != 0:
                    success.append(serializer.data)
            else:
                errors.append(serializer.errors)

        if len(errors) > 0:
            resp_status = status.HTTP_400_BAD_REQUEST
        else:
            resp_status = status.HTTP_200_OK
        return Response({"success_count": len(success), "errors_count": len(errors), "success": success,
                         "errors": errors}, status=resp_status)

    # GET : Affiche la liste
    @prebucquage.mapping.get
    def prebucquage_list(self, request):
        queryset = ParticipationEvent.objects.filter(
            Q(product_participation__parent_event__etat_event=Event.EtatEventChoices.PREBUCQUAGE)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    ### /bucquage/ ###
    # POST : Prends une liste de Bucquage format: [{cible_participation:<id>, product_participation:<id>, quantity:<int>}, ... ] ou
    # simplement {cible_participation:<id>, product_participation:<id>, quantity:<int>}
    @action(methods=['POST'], detail=False)
    def bucquage(self, request):
        user = Utilisateur.objects.get(pk=request.user.pk)
        success = []
        errors = []

        if type(request.data) is QueryDict or type(request.data) is dict:
            datas = [request.data]
        else:
            datas = request.data
        serializer = self.get_serializer(data=datas, many=True, context={'request': request})

        if serializer.is_valid():
            def message_bucquage_valide(cible_participation_id, product_participation_id):
                return {"cible_participation_id": cible_participation_id, "product_participation_id": product_participation_id, "status": "Participation bucquée"}
            def message_bucquage_non_valide(cible_participation_id, product_participation_id, error):
                return {"cible_participation_id": cible_participation_id, "product_participation_id": product_participation_id, "error": error}

            #TODO: vérification du solde de chaque consommateur par rapport au total des buquages

            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            errors = []
            liste_ids = [(p_data.get("cible_participation"),p_data.get("product_participation")) for p_data in datas]
            for index in range(len(liste_ids)):
                err = serializer.errors[index]
                if err != {}:
                    errors.append({"cible_participation": liste_ids[index][0],
                                   "product_participation": liste_ids[index][1],
                                   "error(s)": err})
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    # GET : Affiche la liste
    @bucquage.mapping.get
    def bucquage_list(self, request):
        queryset = ParticipationEvent.objects.filter(
            Q(product_participation__parent_event__etat_event=Event.EtatEventChoices.BUCQUAGE)
        )
        if not self.request.user.has_perm("appevents.event_super_manager"):
            consommateur = Consommateur.objects.get(consommateur=self.request.user)
            queryset = queryset.filter(product_participation__parent_event__managers=consommateur)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    ### /debucquage/ ###
    # POST : Prends une liste de Debucquage format: [{id_participation:<id>, (optionel) negats:<True|False>}, ... ] ou
    # simplement {id_participation:<id>, (optionnel) negats:<True|False>}
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
            participations_request = {p_data.get("id"): p_data.get("negatss") for p_data in serializer.validated_data}
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

            return Response({"success_count": len(success), "errors_count": len(errors), "success": success,
                             "errors": errors}, status=status.HTTP_200_OK)

        else:
            errors = []
            liste_id = [p_data.get("participation_id") for p_data in datas]
            for index in range(len(liste_id)):
                err = serializer.errors[index]
                if err != {}:
                    errors.append({"participation_id": liste_id[index], "status": err})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # GET : Affiche la liste
    @debucquage.mapping.get
    def debucquage_list(self, request):
        queryset = ParticipationEvent.objects.filter(
            Q(product_participation__parent_event__etat_event=Event.EtatEventChoices.DEBUCQUAGE)
        )
        # pas de filtre supplémentaire car il faut la permission appevents.event_super_manager pour cet endpoint
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


# Le paramètre finss est obligatoire et correspond à l'id de l'event
# On peut filtrer/trier les participations par nom, prénom, bucque, fams, proms
# Renvoi toutes les participations classées par Consommateur :
#                                  [{ consommateur_id, nom, prenom, bucque, fams, proms, solde,
#                                     participation:[liste des participations de l'utilisateur
#                                   },
#                                   ...]

class EventParticipationByConsommateurEmptyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (RequiersConsommateur, BucquageEventPermission,)
    http_method_names = ["get", "options"]
    filter_backends = [filters.SearchFilter, CaseInsensitiveOrderingFilter]
    search_fields = ["consommateur__first_name", "consommateur__last_name", "consommateur__bucque", "consommateur__fams", "consommateur__proms"]
    ordering_fields = ["prenom", "nom", "bucque", "fams", "proms"]
    ordering_case_insensitive_fields = ["consommateur__first_name", "consommateur__last_name", "consommateur__bucque", "consommateur__proms"]
    replace_ordering_fields = {"nom": "consommateur__last_name",
                               "prenom": "consommateur__first_name",
                               "fams": "consommateur__fams",
                               "proms": "consommateur__proms",
                               "bucque": "consommateur__bucque"}


# Endpoint pour récupérer les participations prébuquées, par utilisateur, pour un finss donné
class EventPrebucqagesViewSet(EventParticipationByConsommateurEmptyViewSet):
    serializer_class = EventPrebucqagesSerializer

    def get_queryset(self):
        finss_id = self.request.query_params.get("finss", None)
        if finss_id is None:
            return Consommateur.objects.none()
        if not finss_id.isdigit():
            return Consommateur.objects.none()

        return Consommateur.objects.filter(
            participation_event__product_participation__parent_event__pk=finss_id,
            participation_event__prebucque_quantity__gt=0
        ).distinct()


# Endpoint pour récupérer les participations buquées, par utilisateur, pour un finss donné
class EventBucqagesViewSet(EventParticipationByConsommateurEmptyViewSet):
    serializer_class = EventBucquagesSerializer

    def get_queryset(self):
        finss_id = self.request.query_params.get("finss", None)
        if finss_id is None:
            return Consommateur.objects.none()
        if not finss_id.isdigit():
            return Consommateur.objects.none()

        return Consommateur.objects.filter(
            participation_event__product_participation__parent_event__pk=finss_id,
            participation_event__participation_bucquee=True
        ).distinct()


# Endpoint pour récupérer les participations débucquée/à débucquée, par utilisateur, pour un finss donné
class EventDebucqagesViewSet(EventParticipationByConsommateurEmptyViewSet):
    serializer_class = EventDebucquagesSerializer

    def get_queryset(self):
        finss_id = self.request.query_params.get("finss", None)
        if finss_id is None:
            return Consommateur.objects.none()
        if not finss_id.isdigit():
            return Consommateur.objects.none()

        display_debucquee = True if self.request.query_params.get("displayDebucquee", None) == "true" else False

        # si display_debucquee est False, on ne guarde que les consommateur dont au moins une des participations n'est
        # pas débucquée (et que la quantité bucquée est > 0)
        if display_debucquee:
            queryset = Consommateur.objects.filter(
                participation_event__product_participation__parent_event__pk=finss_id,
                participation_event__participation_bucquee=True
            ).distinct()
        else:
            queryset = Consommateur.objects.filter(
                participation_event__product_participation__parent_event__pk=finss_id,
                participation_event__participation_bucquee=True,
                participation_event__participation_debucquee=False,
                participation_event__quantity__gt=0
            ).distinct()

        return queryset
