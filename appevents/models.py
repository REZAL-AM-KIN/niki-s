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
    date_event = models.DateTimeField()
    created_by = models.ForeignKey(
        User, on_delete=CASCADE, editable=False, verbose_name="Créé par", related_name="created_by"
    )

    class EtatEventChoices(models.IntegerChoices):
        PREBUCQUAGE = 1, "Prébucquage"
        BUCQUAGE = 2, "Bucquage"
        DEBUCQUAGE = 3, "Débucquage"
        TERMINE = 4, "Terminé"

    etat_event = models.PositiveSmallIntegerField(
        choices=EtatEventChoices.choices, default=EtatEventChoices.PREBUCQUAGE, verbose_name="Etat de l'évènement", editable=False
    )

    # Les managers sont des consommateurs plutôt que des User car les user sans consommateur ne peuvent pas intéragir
    # avec le front kfet
    managers = models.ManyToManyField(Consommateur, related_name="finss_manages", blank=True)

    def __str__(self):
        return self.titre + " - " + str(self.date_event)

    class Meta:
        permissions = [
            ("event_super_manager", "Autorise l'administration de tous les évenements."),
            ("event_debucquage_negats", "Autorise le débucquage des produits d'un évenement en négatif."),
        ]

    def end(self, *args, **kwargs):
        self.etat_event = self.EtatEventChoices.TERMINE
        self.save()

    def mode_bucquage(self, *args, **kwargs):
        self.etat_event = self.EtatEventChoices.BUCQUAGE
        self.save()

    def mode_debucquage(self, *args, **kwargs):
        self.etat_event = self.EtatEventChoices.DEBUCQUAGE
        self.save()

    def mode_prebucquage(self, *args, **kwargs):
        self.etat_event = self.EtatEventChoices.PREBUCQUAGE
        self.save()


class ProductEvent(models.Model):
    parent_event = models.ForeignKey("Event", on_delete=CASCADE)
    nom = models.CharField(max_length=50)
    description = models.CharField(max_length=200, default=None, blank=True)
    prix_total = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True)
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
    def save(self, *args, **kwargs):http://localhost:8000/api/bucquagevent/3/
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

    @property
    def prix_total(self):
        return self.product_participation.getPrixUnitaire()*Decimal(self.quantity)


    def test_debucquage(self, debucqueur, negats=False):
        if self.product_participation.parent_event.etat_event != Event.EtatEventChoices.DEBUCQUAGE:
            return "L'event n'est pas en mode débucquage"
        if not self.participation_bucquee:
            return "La participation n'est pas bucquée"
        if self.participation_debucquee:
            return "La participation est déjà débucquée"
        if self.cible_participation.activated is False:
            return "Consommateur désactivé"
        if negats and not debucqueur.has_perm("appevents.event_debucquage_negats"):
            return "Vous n'avez pas la permission de débucquer en négatif"
        if negats or Consommateur.testdebit(self.cible_participation, self.prix_total):
            return True
        else:
            return "Le consommateur n'a pas assez d'argent pour ce produit"


    def debucquage(self, debucqueur, negats=False):
        res = self.test_debucquage(debucqueur, negats)
        if res is not True:
            return res

        if self.quantity == 0:
            self.participation_debucquee = True
            self.save()
            return True

        prix_total = self.prix_total

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
        return "Le consommateur n'a pas assez d'argent pour ce produit"

