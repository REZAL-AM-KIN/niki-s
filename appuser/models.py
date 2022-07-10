import base64
import hashlib
import os
from datetime import date

from django.contrib.auth.models import User
from django.db import models

from niki.settings import WITHLDAP


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
    ldap_password = models.CharField(max_length=200, blank=True, editable=False)

    def set_password(self, password):
        super(Utilisateur, self).set_password(password)
        salt = os.urandom(4)
        h = hashlib.sha1(password.encode("utf-8"))
        h.update(salt)
        self.ldap_password = base64.b64encode(h.digest() + salt).strip().decode("utf-8")

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        if WITHLDAP:
            if self.is_active:
                if LdapUser.objects.filter(full_name=self.username).count() == 1:
                    ldapuser_to_modify = LdapUser.objects.get(full_name=self.username)
                    ldapuser_to_modify.email = self.email
                    ldapuser_to_modify.first_name = self.first_name
                    ldapuser_to_modify.last_name = self.last_name
                    ldapuser_to_modify.password = self.ldap_password
                    ldapuser_to_modify.save(force_update=True)
                else:
                    ldapuser_to_save = LdapUser(
                        full_name=self.username,
                        email=self.email,
                        first_name=self.first_name,
                        last_name=self.last_name,
                        password=self.ldap_password,
                    )
                    ldapuser_to_save.save()
            else:
                if LdapUser.objects.filter(full_name=self.username).count() == 1:
                    ldapuser_to_delete = LdapUser.objects.get(full_name=self.username)
                    ldapuser_to_delete.delete()
        if self.date_expiration == "" and self.has_cotiz is True:
            self.date_expiration = date.today
        super(Utilisateur, self).save(*args, **kwargs)


if WITHLDAP:
    try:
        from ldapdb.models import Model as LDAPModel
        from ldapdb.models.fields import PasswordField, CharField, DateTimeField
    except ImportError:
        pass

    class LdapUser(LDAPModel):
        """
        Class for representing an LDAP user entry.
        """

        # LDAP meta-data
        base_dn = "ou=users,dc=rezal,dc=fr"
        object_classes = ["inetOrgPerson"]
        last_modified = DateTimeField(db_column="modifyTimestamp", editable=False)

        # inetOrgPerson
        first_name = CharField(db_column="givenName", verbose_name="Prime name")
        last_name = CharField("Final name", db_column="sn")
        full_name = CharField(db_column="cn", primary_key=True)
        email = CharField(db_column="mail")
        password = PasswordField(db_column="userPassword")

        def __str__(self):
            return self.first_name

        def __unicode__(self):
            return self.full_name
