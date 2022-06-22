# -*- coding: utf-8 -*-

from datetime import date

from django.contrib.auth.models import User
from django.db import models
from niki.settings import WITHLDAP
if WITHLDAP:
    import ldapdb.models
    from ldapdb.models.fields import (PasswordField, CharField, DateTimeField)  


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
        if WITHLDAP:
            if self.is_active:
                if LdapUser.objects.filter(full_name=self.username).count() == 1:
                    ldapuser_to_modify=LdapUser.objects.get(full_name=self.username)
                    ldapuser_to_modify.email=self.email
                    ldapuser_to_modify.first_name=self.first_name
                    ldapuser_to_modify.last_name=self.last_name
                    ldapuser_to_modify.password=self.password
                    ldapuser_to_modify.save(force_update=True)
                else:
                    ldapuser_to_save=LdapUser(full_name=self.username, email=self.email, first_name=self.first_name, last_name=self.last_name, password=self.password)
                    ldapuser_to_save.save()
            else:
                if LdapUser.objects.filter(full_name=self.username).count() == 1:
                    ldapuser_to_delete=LdapUser.objects.get(full_name=self.username)
                    ldapuser_to_delete.delete()
        if self.date_expiration == "" and self.has_cotiz == True:
            self.date_expiration = date.today
        super(Utilisateur, self).save(*args, **kwargs)

class LdapUser(ldapdb.models.Model):
    """
    Class for representing an LDAP user entry.
    """
    # LDAP meta-data
    base_dn = "ou=users,dc=rezal,dc=fr"
    object_classes = ['inetOrgPerson']
    last_modified = DateTimeField(db_column='modifyTimestamp', editable=False)

    # inetOrgPerson
    first_name = CharField(db_column='givenName', verbose_name="Prime name")
    last_name = CharField("Final name", db_column='sn')
    full_name = CharField(db_column='cn', primary_key=True)
    email = CharField(db_column='mail')
    password = PasswordField(db_column='userPassword')

    def __str__(self):
        return self.first_name

    def __unicode__(self):
        return self.full_name