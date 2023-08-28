from datetime import datetime
from random import randint

from django.contrib.admin.utils import lookup_field
from django.db.models import Q
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.fields import MultipleChoiceField
from rest_framework.response import Response

from appevents.models import Event, ProductEvent, ParticipationEvent
from appkfet.models import *
from lydia.models import *
from appuser.models import Groupe

# Assume that you have installed requests: pip install requests
import requests
import json
import uuid

from niki.settings import CASHIER_PHONE, LYDIA_URL, VENDOR_TOKEN


class PermissionsSerializer(serializers.Serializer):
    all = serializers.BooleanField()
    ipIdentification = serializers.ListField(
        child=serializers.CharField()
    )
    groupes = serializers.ListField(
        child=serializers.CharField()
    )
    entities = serializers.ListField(
        child=serializers.CharField()
    )
    #entities = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    entities_manageable = serializers.ListField(
        child=serializers.CharField()
    )
    # = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    recharge = serializers.BooleanField()


########################
#         KFET         #
########################
class ProduitSerializer(serializers.HyperlinkedModelSerializer):
    #on renvoie le nom de l'entite
    entite = serializers.SlugRelatedField(queryset=Entity.objects.all(), slug_field='nom')
    class Meta:
        model = Produit
        fields = ("id", "raccourci", "nom", "prix", "entite")

    def create(self, validated_data):
        #on verifie que l'utilisateur à les permissions pour manager l'entité où il crée le produit
        #permet de résoudre les requêtes avec le nom de l'entité ou l'objet entité
        request = self.context.get("request")
        try:
            entite = Entity.objects.get(
                nom=validated_data["entite"]
            )
        except Entity.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve entity name")

        #on vérifie les permissions
        #soit l'utilisateur peut manager specifiquement l'entité, soit il a la permession de manager tout les produits
        utilisateur = Utilisateur.objects.get(pk=request.user.pk)
        if utilisateur.entities_manageable.filter(nom=entite).exists() or request.user.has_perm("appkfet.produit_super_manager"):
            validated_data["entite"]=entite
            return Produit.objects.create(**validated_data)
        else:
            raise serializers.ValidationError("Cannot create product in this entity")

    def update(self, instance, validated_data):
        #on verifie que l'utilisateur à les permissions pour manager l'entité actuelle et celle visé du produit
        #on vérifie que l'id de l'entite vise est correct
        request = self.context.get("request")
        #permet de résoudre les requêtes avec le nom de l'entité ou l'objet entité
        try:
            entite_vise = Entity.objects.get(
                nom=validated_data["entite"]
            )
        except Entity.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve entity name")

        #soit l'utilisateur peut manager specifiquement les 2 entités, soit il a la permession de manager tout les produits
        #(super_user accord toutes les permission, donc on ne vérifie pas ça en plus)
        utilisateur = Utilisateur.objects.get(pk=request.user.pk)
        if (utilisateur.entities_manageable.filter(nom=entite_vise).exists() and utilisateur.entities_manageable.filter(nom=instance.entite).exists() ) or utilisateur.has_perm("appkfet.produit_super_manager"):
            #on modifie l'entite à la main et on laisse faire le reste à la methode update de la classe. c'est elle qui va appeler la méthode save() de l'instance
            validated_data["entite"]=entite_vise
            return super(ProduitSerializer, self).update(instance, validated_data)
        else:
            if not(utilisateur.entities_manageable.filter(nom=instance.entite).exists()):
                raise serializers.ValidationError("Cannot edit product from entity '"+instance.entite+"'")
            if not(utilisateur.entities_manageable.filter(nom=entite_vise).exists()):
                raise serializers.ValidationError("Cannot add product in entity '"+entite_vise.nom+"'")


class EntiteSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Entity
        fields = ("id", "nom", "description", "color")


class ConsommateurSerializer(serializers.HyperlinkedModelSerializer):
    prenom = serializers.CharField(source="consommateur.first_name", read_only=True)
    bucque = serializers.CharField(source="consommateur.bucque", read_only=True)
    fams = serializers.CharField(source="consommateur.fams", read_only=True)
    proms = serializers.CharField(source="consommateur.proms", read_only=True)
    nom = serializers.CharField(source="consommateur.last_name", read_only=True)

    class Meta:
        model = Consommateur
        fields = ("id", "prenom", "commentaire", "bucque", "fams", "proms", "nom", "solde", "totaldep")


class RechargeSerializer(serializers.HyperlinkedModelSerializer):
    cible_id = serializers.CharField(source="cible_recharge.id")
    date = serializers.DateTimeField(read_only=True)
    initiateur_evenement = serializers.CharField(source="initiateur_evenement.bucque", read_only=True)

    class Meta:
        model = Recharge
        fields = ("cible_id", "montant", "methode", "date", "initiateur_evenement")

    def create(self, validated_data):
        request = self.context.get("request")
        try:
            consommateur = Consommateur.objects.get(
                pk=validated_data["cible_recharge"]["id"]
            )
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve cible id")
        validated_data["cible_recharge"] = consommateur
        validated_data["initiateur_evenement"] = Utilisateur.objects.get(id=request.user.pk)
        validated_data["date"] = datetime.now()
        return Recharge.objects.create(**validated_data)


class BucquageSerializer(serializers.HyperlinkedModelSerializer):
    cible_bucquage = serializers.CharField(source="cible_bucquage.id")
    date = serializers.DateTimeField(read_only=True)
    nom_produit = serializers.CharField(read_only=True)
    prix_produit = serializers.CharField(read_only=True)
    entite_produit = serializers.CharField(read_only=True)
    initiateur_evenement = serializers.CharField(source="initiateur_evenement.bucque", read_only=True)
    id_produit = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = Bucquage
        fields = (
            "cible_bucquage",
            "nom_produit",
            "prix_produit",
            "entite_produit",
            "date",
            "initiateur_evenement",
            "id_produit",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        bucqueur = Utilisateur.objects.get(pk=request.user.pk)
        try:
            consommateur = Consommateur.objects.get(
                pk=validated_data["cible_bucquage"]["id"]
            )
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve cible id")
        try:
            produit = Produit.objects.get(id=validated_data["id_produit"])
            validated_data.pop("id_produit")
        except Produit.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve product name")
        if consommateur.activated is False:
            raise serializers.ValidationError("Consommateur is not activated")
        if consommateur.solde - produit.prix < 0:
            raise serializers.ValidationError("Consommateur has not enough money")
        if (
            bucqueur.entities.filter(pk=produit.entite.pk).exists()
            or bucqueur.is_superuser
        ):
            validated_data["cible_bucquage"] = consommateur
            validated_data["date"] = datetime.now()
            validated_data["nom_produit"] = produit.nom
            validated_data["prix_produit"] = produit.prix
            validated_data["entite_produit"] = produit.entite
            validated_data["initiateur_evenement"] = Utilisateur.objects.get(id=request.user.pk)
            return Bucquage.objects.create(**validated_data)
        else:
            raise serializers.ValidationError("Cannot sell this product")

class HistorySerializer(serializers.HyperlinkedModelSerializer):
    cible_evenement = ConsommateurSerializer()
    initiateur_evenement = serializers.CharField(source="initiateur_evenement.bucque", read_only=True)

    class Meta:
        model = History
        fields = (
            "cible_evenement",
            "nom_evenement",
            "prix_evenement",
            "entite_evenement",
            "date_evenement",
            "initiateur_evenement",
        )

#########################
#         LYDIA         #
#########################


class RechargeLydiaSerializer(serializers.HyperlinkedModelSerializer):
    cible_id = serializers.CharField(source="cible_recharge.id")
    date = serializers.DateTimeField(read_only=True)
    transaction_lydia = serializers.CharField(read_only=True)
    internal_uuid = serializers.CharField(read_only=True)

    class Meta:
        model = RechargeLydia
        fields = ("cible_id", "montant", "qrcode", "date", "transaction_lydia", "internal_uuid")

    def create(self, validated_data):
        request = self.context.get("request")
        # récupération du consommateur
        try:
            consommateur = Consommateur.objects.get(
                pk=validated_data["cible_recharge"]["id"]
            )
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve cible id")
        # définition du json à envoyer à Lydia
        internal_uuid = uuid.uuid1()
        data_object = {
            'vendor_token': VENDOR_TOKEN,
            'phone': CASHIER_PHONE,
            'paymentData': validated_data["qrcode"],
            'amount': str(validated_data["montant"]),
            'currency': "EUR",
            'order_id': internal_uuid.hex,
        }
        # définition de l'url du endpoint
        url_encaissement = LYDIA_URL+"/api/payment/payment.json"
        # requête Lydia POST /api/payment/payment au format json
        r = requests.post(url_encaissement, data=data_object)
        r_status = r.status_code
        # si le call a marché
        if r_status == 200:
            # récupération de la réponse
            response = json.loads(r.text)
            try:
                # si la transaction est un succès, j'aurais un transaction identifier, sinon non !
                transaction_lydia = response["transaction_identifier"]
                # création de l'objet en base
                validated_data["transaction_lydia"] = transaction_lydia
                validated_data["cible_recharge"] = consommateur
                validated_data["initiateur_evenement"] = Utilisateur.objects.get(id=request.user.pk)
                validated_data["date"] = datetime.now()
                validated_data["internal_uuid"] = internal_uuid.hex
                return RechargeLydia.objects.create(**validated_data)
            except:
                pass
            message = "An error occured with Lydia : Error " + response["error"] + " : " + response["message"]
            raise serializers.ValidationError(message)
        else:
            raise serializers.ValidationError("An error occured with Lydia")


########################
#        FIN'SS        #
########################
class EventSerializer(serializers.HyperlinkedModelSerializer):
    can_manage = serializers.SerializerMethodField(read_only=True)
    is_prebucque = serializers.SerializerMethodField(read_only=True)
    managers = serializers.PrimaryKeyRelatedField(many=True, queryset=Consommateur.objects.all())

    class Meta:
        model = Event
        fields = ("id", "titre", "description", "can_subscribe", "date_event", "ended", "can_manage", "is_prebucque",
                  "managers")

    # Regarde si l'utilisateur qui fait la requete est dans la liste des managers
    def get_can_manage(self, obj):
        request = self.context.get('request')

        # On vérifie si l'utilisateur est super user ou super manager
        if request.user.is_superuser or request.user.has_perm("appevents.event_super_manager"):
            return True

        # Sinon on regarde si l'utilisateur est dans la liste des managers du fin'ss
        consommateur = Consommateur.objects.get(consommateur=request.user)
        return obj.managers.filter(id=consommateur.id).exists()

    # Regarde sur l'utilisateur à déjà une participation enregistré pour ce fin'ss
    def get_is_prebucque(self, obj):
        user = self.context.get('request').user
        consommateur = Consommateur.objects.get(consommateur=user)
        participations = consommateur.participation_event.all()        # On récupère toute les participations de l'utilisateur

        return participations.filter(product_participation__parent_event=obj).exists()  # On check l'existence de participation pour le fin'ss

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = Utilisateur.objects.get(id=request.user.pk)
        managers = validated_data.pop("managers")
        event = Event.objects.create(**validated_data)
        event.managers.set(managers)
        return event


class ProductEventSerializer(serializers.HyperlinkedModelSerializer):
    quantite_prebucque = serializers.SerializerMethodField(read_only=True)
    quantite_bucque = serializers.SerializerMethodField(read_only=True)
    parent_event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    prix_unitaire = serializers.SerializerMethodField(read_only=True)
    prix_total = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    prix_min = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

    class Meta:
        model = ProductEvent
        fields = ("id", "parent_event", "nom", "description", "prix_total", "prix_min", "obligatoire", "quantite_prebucque", "quantite_bucque", "prix_unitaire")

    def get_quantite_prebucque(self, product):
        qts = 0
        participations = ParticipationEvent.objects.filter(product_participation=product)
        for participation in participations:
            qts += participation.prebucque_quantity
        return qts

    def get_quantite_bucque(self, product):
        qts = 0
        participations = ParticipationEvent.objects.filter(Q(product_participation=product) & Q(participation_bucquee=True))
        for participation in participations:
            qts += participation.quantity
        return qts

    def get_prix_unitaire(self, product):
        prix = product.getPrixUnitaire()
        if prix is None:
            return None
        return str(round(product.getPrixUnitaire(), 2))


class ParticipationEventSerializer(serializers.HyperlinkedModelSerializer):
    cible_participation = serializers.PrimaryKeyRelatedField(queryset=Consommateur.objects.all())
    product_participation = serializers.PrimaryKeyRelatedField(queryset=ProductEvent.objects.all())
    participation_debucquee = serializers.BooleanField(read_only=True)

    class Meta:
        model = ParticipationEvent
        fields = ("id", "cible_participation", "product_participation", "prebucque_quantity", "quantity", "participation_bucquee", "participation_debucquee")

    # On surcharge create pour faire une update si a participation existe déjà
    def create(self, validated_data):
        # les critères de recherche pour une participation existantes sont la cible et le produit
        # --> si une participation existe déjà, alors elle est update avec les validated_data
        participation, created = ParticipationEvent.objects.update_or_create(
            cible_participation=validated_data.get("cible_participation"),
            product_participation=validated_data.get("product_participation"), defaults=validated_data)
        return participation


# Serializer pour les débucquages
class DebucquageEventSerializer(serializers.Serializer):
    participation_id = serializers.IntegerField(default=-1)
    negatss = serializers.BooleanField(default=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


# Serializer pour l'affichage des bucquages classés par consommateur
class BucquageEventSerializer(ConsommateurSerializer):
    consommateur_id = serializers.IntegerField(source="id", read_only=True)
    consommateur_bucque = serializers.CharField(source="consommateur.bucque", read_only=True)
    consommateur_nom = serializers.CharField(source="consommateur.last_name", read_only=True)
    consommateur_fams = serializers.CharField(source="consommateur.fams", read_only=True)
    participation_event = serializers.SerializerMethodField()

    class Meta:
        model = Consommateur
        fields = (
        "consommateur_id", "consommateur_bucque", "consommateur_nom", "consommateur_fams", "participation_event")

    def get_participation_event(self, consommateur):
        request = self.context.get("request")
        queryset = ParticipationEvent.objects.filter(
            Q(cible_participation=consommateur)
            & Q(product_participation__parent_event__ended=False)
        )

        # Dans le cas ou l'utilisateur n'est pas superuser ou supermanager, il faut que les participations affichées
        # soit uniquement les participations qui correspondent aux fin'ss dont l'utilisateur est manager.
        # On filtre donc les participations
        if not request.user.has_perm("appevents.event_super_manager") and not request.user.is_superuser:
            requester_consom = Consommateur.objects.get(consommateur=request.user)
            managed_events = Event.objects.filter(managers=requester_consom)
            if managed_events.count() != 0:
                queryset = queryset.filter(product_participation__parent_event__in=managed_events)

        finss_id = request.query_params.get("finss", None)

        # Si un finss_id est donné, alors on filtre les Participations
        if finss_id is not None:
            if not finss_id.isdigit():
                queryset = queryset.none()
            else:
                queryset = queryset.filter(product_participation__parent_event__pk=finss_id)

        serializer = ParticipationEventSerializer(instance=queryset, many=True)
        return serializer.data
