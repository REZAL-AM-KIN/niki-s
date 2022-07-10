from datetime import datetime

from rest_framework import serializers

from appkfet.models import *


########################
#         KFET         #
########################


class ProduitSerializer(serializers.HyperlinkedModelSerializer):
    nom_entite = serializers.CharField(source="entite.name", read_only=True)

    class Meta:
        model = Produit
        fields = ("id", "nom", "prix", "nom_entite")


class ConsommateurSerializer(serializers.HyperlinkedModelSerializer):
    consommateur_nom = serializers.CharField(
        source="consommateur.username", read_only=True
    )

    class Meta:
        model = Consommateur
        fields = ("id", "consommateur_nom", "solde", "totaldep")


class RechargeSerializer(serializers.HyperlinkedModelSerializer):
    cible_id = serializers.CharField(source="cible_recharge.id")
    date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Recharge
        fields = ("cible_id", "montant", "methode", "date")

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

    class Meta:
        model = Bucquage
        fields = (
            "cible_bucquage",
            "nom_produit",
            "prix_produit",
            "entite_produit",
            "date",
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
    class Meta:
        model = History
        fields = (
            "cible_evenement",
            "nom_evenement",
            "prix_evenement",
            "entite_evenement",
            "date_evenement",
        )
