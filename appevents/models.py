from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import CASCADE

from appkfet.models import Consommateur, History


class Event(models.Model):
    titre = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    can_subscribe = models.BooleanField(
        default=True, verbose_name="Ouvert à l'inscription"
    )
    date_event = models.DateTimeField()
    created_by = models.ForeignKey(
        User, on_delete=CASCADE, editable=False, verbose_name="Créé par"
    )
    ended = models.BooleanField(default=False, verbose_name="Evènement terminé")
    report = models.FileField(blank=True, upload_to="report/", editable=False)

    def __str__(self):
        return self.titre + " - " + str(self.date_event)


class ProductEvent(models.Model):
    parent_event = models.ForeignKey("Event", on_delete=CASCADE)
    nom = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    prix = models.DecimalField(max_digits=5, decimal_places=2)
    obligatoire = models.BooleanField(default=False)

    def __str__(self):
        return str(self.parent_event) + " - " + self.nom


class ParticipationEvent(models.Model):
    cible_participation = models.ForeignKey(Consommateur, on_delete=CASCADE)
    product_participation = models.ForeignKey(ProductEvent, on_delete=CASCADE)
    number = models.IntegerField(default=1, verbose_name="Quantité")
    participation_ok = models.BooleanField(default=False)
    participation_bucquee = models.BooleanField(default=False)

    def __unicode__(self):
        return self.pk

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
            super(ParticipationEvent, self).save(*args, **kwargs)
