# -*- coding: utf-8 -*-

from unicodedata import decimal
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.deletion import CASCADE

from appuser.models import Utilisateur


# Create your models here.


class Consommateur(models.Model):
    consommateur = models.ForeignKey("appuser.Utilisateur", on_delete=CASCADE)
    solde = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    totaldep = models.DecimalField(max_digits=5, decimal_places=2, default=0, editable=False)
    activated=models.BooleanField(default=True)

    def __str__(self):
        utilisateur = Utilisateur.objects.get(pk=self.consommateur)
        return utilisateur.username

    def credit(self, montant):
        self.solde += montant
        self.save()

    def testdebit(self, montant):
        statut = False
        if self.solde >= montant:
            statut = True
        return statut

    def debit(self, montant):
        self.solde -= montant
        self.totaldep += montant
        self.save()


class Produit(models.Model):
    nom = models.CharField(max_length=50)
    prix = models.DecimalField(max_digits=5, decimal_places=2)
    raccourci = models.CharField(max_length=3)
    entite = models.ForeignKey(Group, on_delete=CASCADE)

    def __str__(self):
        return self.nom


class Recharge(models.Model):
    CHOIX_METHODE = [
        ("CB", "Carte bleue"),
        ("Espèces", "Espèces"),
        ("Chèque", "Chèque"),
        ("Lydia", "Lydia"),
    ]
    cible_recharge = models.ForeignKey("Consommateur", on_delete=CASCADE)
    date = models.DateTimeField()
    montant = models.DecimalField(max_digits=5, decimal_places=2)
    methode = models.CharField(max_length=50, choices=CHOIX_METHODE)
    solde_before = models.DecimalField(max_digits=5, decimal_places=2)
    solde_after = models.DecimalField(max_digits=5, decimal_places=2)

    def save(self, *args, **kwargs):
        self.solde_before = self.cible_recharge.solde
        self.solde_after = self.cible_recharge.solde + self.montant
        super(Recharge, self).save(*args, **kwargs)
        Consommateur.credit(self.cible_recharge, self.montant)
        History.objects.update_or_create(
            cible_evenement=self.cible_recharge,
            nom_evenement="Recharge "+self.methode,
            prix_evenement=self.montant,
            entite_evenement="Recharge",
            date_evenement=self.date
            )


    def __unicode__(self):
        return self.pk


class Bucquage(models.Model):
    cible_bucquage = models.ForeignKey("Consommateur", on_delete=CASCADE)
    date = models.DateTimeField()
    nom_produit = models.CharField(max_length=50)
    prix_produit = models.DecimalField(max_digits=5, decimal_places=2)
    entite_produit = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        if Consommateur.testdebit(self.cible_bucquage, self.prix_produit):
            super(Bucquage, self).save(*args, **kwargs)
            Consommateur.debit(self.cible_bucquage, self.prix_produit)
            History.objects.update_or_create(
                cible_evenement=self.cible_bucquage,
                nom_evenement=self.nom_produit,
                prix_evenement=self.prix_produit,
                entite_evenement=self.entite_produit,
                date_evenement=self.date
            )

    def __unicode__(self):
        return self.pk


class History(models.Model):
    cible_evenement=models.ForeignKey("Consommateur", on_delete=CASCADE)
    nom_evenement=models.CharField(max_length=200)
    prix_evenement=models.DecimalField(max_digits=5, decimal_places=2)
    entite_evenement=models.CharField(max_length=200)
    date_evenement=models.DateTimeField()

    def __unicode__(self):
        return self.pk