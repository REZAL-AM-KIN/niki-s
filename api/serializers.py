from datetime import datetime
from random import randint

from rest_framework import serializers

from appkfet.models import *
from lydia.models import *

# Assume that you have installed requests: pip install requests
import requests
import json
import uuid

from niki.settings import CASHIER_PHONE, LYDIA_URL, VENDOR_TOKEN


class PermissionsSerializer(serializers.Serializer):
    all = serializers.BooleanField()
    vpKfet = serializers.BooleanField()
    vpCvis = serializers.BooleanField()


########################
#         KFET         #
########################


class ProduitSerializer(serializers.HyperlinkedModelSerializer):
    nom_entite = serializers.CharField(source="entite.name", read_only=True)

    class Meta:
        model = Produit
        fields = ("id", "nom", "prix", "nom_entite")


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
        try:
            consommateur = Consommateur.objects.get(
                pk=validated_data["cible_recharge"]["id"]
            )
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve cible id")
        validated_data["cible_recharge"] = consommateur
        validated_data["date"] = datetime.now()
        return Recharge.objects.create(**validated_data)


class BucquageSerializer(serializers.HyperlinkedModelSerializer):
    cible_bucquage = serializers.CharField(source="cible_bucquage.id")
    date = serializers.DateTimeField(read_only=True)
    nom_produit = serializers.CharField()
    prix_produit = serializers.CharField(read_only=True)
    entite_produit = serializers.CharField(read_only=True)
    initiateur_evenement = serializers.CharField(source="initiateur_evenement.bucque", read_only=True)

    class Meta:
        model = Bucquage
        fields = (
            "cible_bucquage",
            "nom_produit",
            "prix_produit",
            "entite_produit",
            "date",
            "initiateur_evenement",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        bucqueur = request.user
        try:
            consommateur = Consommateur.objects.get(
                pk=validated_data["cible_bucquage"]["id"]
            )
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve cible id")
        try:
            produit = Produit.objects.get(nom=validated_data["nom_produit"])
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve product name")
        if consommateur.activated is False:
            raise serializers.ValidationError("Consommateur is not activated")
        if consommateur.solde - produit.prix < 0:
            raise serializers.ValidationError("Consommateur has not enough money")
        if (
            bucqueur.groups.filter(name=produit.entite).exists()
            or bucqueur.is_superuser
        ):
            validated_data["cible_bucquage"] = consommateur
            validated_data["date"] = datetime.now()
            validated_data["nom_produit"] = produit.nom
            validated_data["prix_produit"] = produit.prix
            validated_data["entite_produit"] = produit.entite
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
        #récupération du consommateur
        try:
            consommateur = Consommateur.objects.get(
                pk=validated_data["cible_recharge"]["id"]
            )
        except Consommateur.DoesNotExist:
            raise serializers.ValidationError("Cannot resolve cible id")
        #définition du json à envoyer à Lydia
        internal_uuid = uuid.uuid1()
        data_object = {
            'vendor_token': VENDOR_TOKEN,
            'phone': CASHIER_PHONE,
            'paymentData': validated_data["qrcode"],
            'amount': str(validated_data["montant"]),
            'currency': "EUR",
            'order_id': internal_uuid.hex,
        }
        #définition de l'url du endpoint
        url_encaissement = LYDIA_URL+"/api/payment/payment.json"
        #requête Lydia POST /api/payment/payment au format json
        r = requests.post(url_encaissement, data=data_object)
        r_status = r.status_code
        #si le call a marché
        if r_status == 200:
            #récupération de la réponse
            response = json.loads(r.text)
            try:
                #si la transaction est un succès, j'aurais un transaction identifier, sinon non !
                transaction_lydia = response["transaction_identifier"]
                #création de l'objet en base
                validated_data["transaction_lydia"] = transaction_lydia
                validated_data["cible_recharge"] = consommateur
                validated_data["date"] = datetime.now()
                validated_data["internal_uuid"] = internal_uuid.hex
                return RechargeLydia.objects.create(**validated_data)
            except:
                pass
            message = "An error occured with Lydia : Error " + response["error"] + " : " + response["message"]
            raise serializers.ValidationError(message)
        else:
            raise serializers.ValidationError("An error occured with Lydia")
