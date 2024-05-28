from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.deletion import CASCADE

from appkfet.models import Consommateur, History
from appuser.models import Utilisateur


class Event(models.Model):
    titre = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    can_subscribe = models.BooleanField(
        default=True, verbose_name="Ouvert au pré-bucquage"
    )
    date_event = models.DateTimeField()
    created_by = models.ForeignKey(
        User, on_delete=CASCADE, editable=False, verbose_name="Créé par", related_name="created_by"
    )
    ended = models.BooleanField(default=False, verbose_name="Evènement terminé")

    # Les managers sont des consommateurs plutôt que des User car les user sans consommateur ne peuvent pas intéragir
    # avec le front kfet
    managers = models.ManyToManyField(Consommateur, related_name="finss_manages", blank=True)

    def __str__(self):
        return self.titre + " - " + str(self.date_event)

    class Meta:
        permissions = [
            ("event_super_manager", "Autorise l'administration de tous les évenements."),
        ]

    def end(self, *args, **kwargs):
        self.ended = True
        self.save()


class ProductEvent(models.Model):
    parent_event = models.ForeignKey("Event", on_delete=CASCADE)
    nom = models.CharField(max_length=50)
    description = models.CharField(max_length=200, default=None, blank=True)
    prix_total = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    prix_min = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True)
    obligatoire = models.BooleanField(default=False)

    def __str__(self):
        return str(self.parent_event) + " - " + self.nom

    def getPrixUnitaire(self):
        # Determination du nombre de participation bucquee sur le même produit
        participations_identique = ParticipationEvent.objects.filter(
            Q(product_participation=self) & Q(participation_bucquee=True))
        nb_participations = sum([p.quantity for p in participations_identique])

        if nb_participations == 0:
            return None

        prix_unitaire = self.prix_total / nb_participations

        return max(prix_unitaire, self.prix_min)





class ParticipationEvent(models.Model):
    cible_participation = models.ForeignKey(Consommateur, on_delete=CASCADE, related_name="participation_event")
    product_participation = models.ForeignKey(ProductEvent, on_delete=CASCADE)
    prebucque_quantity = models.IntegerField(default=0, verbose_name="Quantité prébucquée")
    quantity = models.IntegerField(default=0, verbose_name="Quantité")
    participation_bucquee = models.BooleanField(default=False)
    participation_debucquee = models.BooleanField(default=False)

    def __unicode__(self):
        return self.pk

    """
    def save(self, *args, **kwargs):
        if self.participation_ok is True and self.participation_bucquee is False:
            prix_total = Decimal(self.number) * self.product_participation.prix
            if Consommateur.testdebit(self.cible_participation, prix_total):
                self.participation_bucquee = True
                super(ParticipationEvent, self).save(*args, **kwargs)
                Consommateur.debit(self.cible_participation, prix_total)
                History.objects.update_or_create(
                    cible_evenement=self.cible_participation,
                    nom_evenement=f"{self.number}x {self.product_participation.parent_event.titre} - "
                    f"{self.product_participation.nom}",
                    prix_evenement=prix_total,
                    entite_evenement="Evènement",
                    date_evenement=self.product_participation.parent_event.date_event,
                )
            else:
                super(ParticipationEvent, self).save(*args, **kwargs)
        else:
            super(ParticipationEvent, self).save(*args, **kwargs)"""

    def debucquage(self, debucqueur, negats=False):
        if self.quantity == 0:
            return "Nothing to debucque"

        if self.participation_bucquee is False:
            return "Participation is not bucquée"
        if self.participation_debucquee:
            return "Participation already débucquée"

        if self.cible_participation.activated is False:
            return "Consommateur is not activated"

        #TODO : vérifiction de permission de débucquage negat'ss


        produit = self.product_participation


        prix_total = produit.getPrixUnitaire()*Decimal(self.quantity)

        if Consommateur.testdebit(self.cible_participation, prix_total) or negats:
            self.participation_debucquee = True
            self.save()
            Consommateur.debit(self.cible_participation, prix_total)
            History.objects.update_or_create(
                initiateur_evenement=debucqueur,
                cible_evenement=self.cible_participation,
                nom_evenement=f"{self.quantity}x {self.product_participation.nom} - "
                              f"{self.product_participation.parent_event.titre}",
                prix_evenement=prix_total,
                entite_evenement="Evènement",
                date_evenement=self.product_participation.parent_event.date_event,
            )
            return True
        return "Consommateur has not enough money"

