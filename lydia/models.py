from django.db import models
from django.db.models.deletion import CASCADE
from appkfet.models import Consommateur, History

# Create your models here.


class RechargeLydia(models.Model):
    cible_recharge = models.ForeignKey("appkfet.Consommateur", on_delete=CASCADE)
    date = models.DateTimeField()
    montant = models.DecimalField(max_digits=5, decimal_places=2)
    qrcode = models.CharField(max_length=200)
    internal_uuid = models.CharField(max_length=200)
    transaction_lydia = models.CharField(max_length=200)
    solde_before = models.DecimalField(max_digits=5, decimal_places=2)
    solde_after = models.DecimalField(max_digits=5, decimal_places=2)
    initiateur_evenement = models.ForeignKey("appuser.Utilisateur", on_delete=CASCADE)

    def save(self, *args, **kwargs):
        self.solde_before = self.cible_recharge.solde
        self.solde_after = self.cible_recharge.solde + self.montant
        super(RechargeLydia, self).save(*args, **kwargs)
        Consommateur.credit(self.cible_recharge, self.montant)
        History.objects.update_or_create(
            cible_evenement=self.cible_recharge,
            nom_evenement="Recharge Lydia",
            prix_evenement=self.montant,
            entite_evenement="Recharge",
            date_evenement=self.date,
            initiateur_evenement=self.initiateur_evenement,
        )

    def __unicode__(self):
        return self.pk
