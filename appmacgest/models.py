from django.core import exceptions
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from appuser.models import Utilisateur
from niki.settings import RADIUS


class Radcheck(models.Model):
    username = models.CharField(max_length=17)
    attribute = models.CharField(max_length=64, default="ClearText-Password")
    op = models.CharField(max_length=2, default=":=")
    value = models.CharField(max_length=64, default="authok")

    class Meta:
        db_table = "radcheck"


def save_in_radcheck(new_device):
    Radcheck.objects.get_or_create(
        username=new_device.mac, attribute="ClearText-Password", op=":=", value="authok"
    )


def delete_in_radcheck(new_device):
    try:
        tmp = Radcheck.objects.filter(username=new_device.mac)
        tmp.all().delete()
    except (exceptions.ObjectDoesNotExist, exceptions.MultipleObjectsReturned):
        return


class Device(models.Model):
    proprietaire = models.ForeignKey("appuser.Utilisateur", on_delete=CASCADE)
    nom = models.CharField(max_length=200)
    mac = models.CharField(
        max_length=17,
        validators=[RegexValidator(regex="^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$")],
    )
    accepted = models.BooleanField(default=False)
    enable = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        super(Device, self).save(*args, **kwargs)
        device_user = Utilisateur.objects.get(pk=self.proprietaire.pk)
        if RADIUS:
            if (
                device_user.has_cotiz
                and self.accepted is True
                and self.enable is True

            ):
                save_in_radcheck(self)
            else:
                delete_in_radcheck(self)

    def delete(self, *args, **kwargs):
        super(Device, self).delete(*args, **kwargs)
        if RADIUS:
            delete_in_radcheck(self)

    def disable(self, *args, **kwargs):
        self.enable = False
        super(Device, self).save(*args, **kwargs)
        if RADIUS:
            delete_in_radcheck(self)


@receiver(post_save, sender=Utilisateur)
def update_device(sender, instance, **kwargs):
    associated_devices = Device.objects.filter(proprietaire=instance.pk)
    if associated_devices != []:
        for device in associated_devices:
            device.save()

