from django.db import models
from appkfet.models import Consommateur, History
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE

# Create your models here.

class Event(models.Model):
    titre=models.CharField(max_length=100)
    description=models.CharField(max_length=200)
    cansubscribe=models.BooleanField(default=True, verbose_name="Ouvert à l'inscription")
    date_event=models.DateTimeField()
    created_by=models.ForeignKey(User, on_delete=CASCADE, editable=False, verbose_name="Créé par")
    ended=models.BooleanField(default=False)

    def __str__(self):
       return self.titre + " - " + str(self.date_event)


class Product_event(models.Model):
    parent_event=models.ForeignKey("Event", on_delete=CASCADE)
    nom=models.CharField(max_length=50)
    description=models.CharField(max_length=200)
    prix=models.DecimalField(max_digits=5, decimal_places=2)
    obligatoire=models.BooleanField(default=False)

    def __str__(self):
        return str(self.parent_event) + " - " + self.nom


class Participation_event(models.Model):
    cible_participation=models.ForeignKey("appkfet.Consommateur", on_delete=CASCADE)
    product_participation=models.ForeignKey("Product_event", on_delete=CASCADE)
    number=models.IntegerField(default=1, verbose_name="Quantité")
    participation_ok=models.BooleanField(default=False)
    participation_bucquee=models.BooleanField(default=False)

    def __unicode__(self):
        return self.pk

    def save(self, *args, **kwargs):
        if self.participation_ok==True:
            prix_total=self.number * self.product_participation.prix
            if Consommateur.testdebit(self.cible_participation, prix_total):
                super(Participation_event, self).save(*args, **kwargs)
                Consommateur.debit(self.cible_participation, prix_total)
                History.objects.update_or_create(
                    cible_evenement=self.cible_participation,
                    nom_evenement=str(self.number) + "x " + self.product_participation.parent_event.titre + " - " + self.product_participation.nom,
                    prix_evenement=prix_total,
                    entite_evenement="Evènement",
                    date_evenement=self.product_participation.parent_event.date_event)
        else:
            super(Participation_event, self).save(*args,**kwargs)