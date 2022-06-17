# -*- coding: utf-8 -*-

from datetime import date

from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class Utilisateur(User):
    chambre = models.CharField(max_length=5)
    phone = models.CharField(max_length=10, verbose_name="Téléphone")
    bucque = models.CharField(blank=True, max_length=200)
    fams = models.CharField(blank=True, max_length=200, verbose_name="Fam's")
    proms = models.CharField(blank=True, max_length=200, verbose_name="Prom's")
    is_gadz = models.BooleanField(default=False)
    is_conscrit = models.BooleanField(default=False)
    has_cotiz = models.BooleanField(default=False)
    date_expiration = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.date_expiration == "" and self.has_cotiz == True:
            self.date_expiration = date.today
        super(Utilisateur, self).save(*args, **kwargs)
