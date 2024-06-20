from django.contrib.auth.models import Group
from django.db import models
from django.db.models.deletion import CASCADE

from appkfet.validators import strictly_positive_validator
from appuser.models import Utilisateur


class Consommateur(models.Model):
    consommateur = models.OneToOneField("appuser.Utilisateur", on_delete=CASCADE)
    solde = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, editable=False
    )
    totaldep = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, editable=False
    )
    commentaire = models.CharField(max_length=50, blank=True)
    activated = models.BooleanField(default=True)

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


# Model utilisé pour stocker les entités disponible sur le site kfet
class Entity(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=7, default="#000000")

    def __str__(self):
        return self.nom

class Produit(models.Model):
    nom = models.CharField(max_length=50)
    prix = models.DecimalField(max_digits=5, decimal_places=2)
    raccourci = models.CharField(max_length=3)
    entite = models.ForeignKey(Entity, on_delete=CASCADE)
    stock = models.SmallIntegerField(blank=True, null=True, default=None)
    suivi_stock = models.BooleanField(default=False, verbose_name="Suivit du stock")

    class Meta:
        permissions = [
            ("produit_super_manager", "Autorise l'administration de tous les produits."),
        ]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        """On définit la valeur du stock à None si on ne suit pas le stock du produit (pour remplacer une précédente
        valeur dans le cas où l'où désactive le suivit), et à 0 si on suit le stock mais qu'il est à None (si on active
        un stock précédement non suivit par exemple)"""
        if not self.suivi_stock:
            self.stock = None
        elif self.stock is None:
            self.stock = 0
        super(Produit, self).save(*args, **kwargs)

    def bucquage(self):
        if self.suivi_stock:
            self.stock -= 1
            self.save()


class Recharge(models.Model):
    CHOIX_METHODE = [
        ("CB", "Carte bleue"),
        ("Espèces", "Espèces"),
        ("Chèque", "Chèque"),
    ]
    cible_recharge = models.ForeignKey("Consommateur", on_delete=CASCADE)
    date = models.DateTimeField()
    montant = models.DecimalField(max_digits=5, decimal_places=2, validators=[strictly_positive_validator])
    methode = models.CharField(max_length=50, choices=CHOIX_METHODE)
    solde_before = models.DecimalField(max_digits=5, decimal_places=2)
    solde_after = models.DecimalField(max_digits=5, decimal_places=2)
    initiateur_evenement = models.ForeignKey("appuser.Utilisateur", on_delete=CASCADE)

    def save(self, *args, **kwargs):
        self.solde_before = self.cible_recharge.solde
        self.solde_after = self.cible_recharge.solde + self.montant
        super(Recharge, self).save(*args, **kwargs)
        Consommateur.credit(self.cible_recharge, self.montant)
        History.objects.update_or_create(
            cible_evenement=self.cible_recharge,
            nom_evenement="Recharge " + self.methode,
            prix_evenement=self.montant,
            entite_evenement="Recharge",
            date_evenement=self.date,
            initiateur_evenement=self.initiateur_evenement,
        )

    def __unicode__(self):
        return self.pk


class Bucquage(models.Model):
    cible_bucquage = models.ForeignKey("Consommateur", on_delete=CASCADE)
    date = models.DateTimeField()
    nom_produit = models.CharField(max_length=50)
    prix_produit = models.DecimalField(max_digits=5, decimal_places=2)
    entite_produit = models.CharField(max_length=50)
    initiateur_evenement = models.ForeignKey("appuser.Utilisateur", on_delete=CASCADE)

    def save(self, *args, **kwargs):
        if Consommateur.testdebit(self.cible_bucquage, self.prix_produit):
            super(Bucquage, self).save(*args, **kwargs)
            Consommateur.debit(self.cible_bucquage, self.prix_produit)
            History.objects.update_or_create(
                cible_evenement=self.cible_bucquage,
                nom_evenement=self.nom_produit,
                prix_evenement=self.prix_produit,
                entite_evenement=self.entite_produit,
                date_evenement=self.date,
                initiateur_evenement=self.initiateur_evenement,
            )

    def __unicode__(self):
        return self.pk


class History(models.Model):
    cible_evenement = models.ForeignKey("Consommateur", on_delete=CASCADE)
    nom_evenement = models.CharField(max_length=200)
    prix_evenement = models.DecimalField(max_digits=5, decimal_places=2)
    entite_evenement = models.CharField(max_length=200)
    date_evenement = models.DateTimeField()
    initiateur_evenement = models.ForeignKey("appuser.Utilisateur", on_delete=CASCADE)

    def __unicode__(self):
        return self.pk



class AuthorizedIP(models.Model):
    groupe = models.ForeignKey("appuser.Groupe", on_delete=CASCADE)
    ip = models.GenericIPAddressField(protocol='IPv4')
    description = models.CharField(max_length=100)

    class Meta:
        permissions = (
            ("bypass_ip_constraint", "N'est pas obligé d'être au pian's pour bucquer"),
        )
