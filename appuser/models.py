# -*- coding: utf-8 -*-

import os
import hashlib
import base64
import hashlib
import os
from datetime import date

from django.contrib.auth.models import User, Group
from django.db import models


from db import WITHLDAP
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch.dispatcher import receiver

try:
    import ldapdb.models
    from ldapdb.models.fields import (PasswordField, CharField, DateTimeField, ListField)  
except:
    pass


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
    ldap_password=models.CharField(max_length=200, blank=True, editable=False)
    max_devices = models.PositiveIntegerField(default=10, verbose_name="Nombre maximal d'appareil")
    last_email_date = models.DateField(null=True, default=None, editable=False)
    
    #surcharge de la méthode set_password pour définir le mot de passe utilisé dans le ldap (hash ssha)
    def set_password(self, password):
        super(Utilisateur, self).set_password(password)
        salt = os.urandom(4)
        h = hashlib.sha1(password.encode("utf-8"))
        h.update(salt)
        self.ldap_password = base64.b64encode(h.digest() + salt).strip().decode("utf-8")


    def save(self, *args, **kwargs):
        if not self.is_active:
            self.has_cotiz=False
        super(Utilisateur, self).save(*args, **kwargs)
    # TODO : Desactivation du consommateur lors de la désactivation du compte

    def __unicode__(self):
        return self.username

    #fonction entities renvoyant la liste des entités auxquelles appartient l'utilisateur en passant par ses groupes
    # Entities est considéré comme un attribut de l'utilisateur
    @property
    def entities(self):
        from appkfet.models import Entity
        return Entity.objects.filter(models.Q(groups__in=self.groups.all()) | models.Q(groups_management__in=self.groups.all())).distinct()

    #fonction entities_manageable renvoyant la liste des entités que l'utilisateur peut gérer en passant par ses groupes
    #entities_manageable est considéré comme un attribut de l'utilisateur
    @property
    def entities_manageable(self):
        from appkfet.models import Entity
        return Entity.objects.filter(groups_management__in=self.groups.all()).distinct()



#surcharge du modèle Group de base pour lui rajouter cet attribut d'entité
class Groupe(Group):
    from appkfet.models import Entity
    entities = models.ManyToManyField(Entity, blank=True, related_name="groups")
    entities_manageable = models.ManyToManyField(Entity, blank=True, related_name="groups_management")


#si l'application fonctionne avec le LDAP, alors : 
if WITHLDAP:

    #définition d'un modèle correspondant à la table ldap user
    class LdapUser(ldapdb.models.Model):
        """
        Class for representing an LDAP user entry.
        """

        # LDAP meta-data
        base_dn = "ou=users,dc=rezal,dc=fr"
        object_classes = ["inetOrgPerson"]
        last_modified = DateTimeField(db_column="modifyTimestamp", editable=False)

        # inetOrgPerson
        first_name = CharField(db_column='givenName', verbose_name="Prime name")
        last_name = CharField("Final name", db_column='sn')
        full_name = CharField(db_column='cn', primary_key=True) #username
        email = CharField(db_column='mail')
        password = PasswordField(db_column='userPassword')
        pk_django = CharField(db_column='uid') #On se base sur la PK django qu'on met dans le champ uid du LDAP

        def __str__(self):
            return self.first_name

        def __unicode__(self):
            return self.full_name

    #lorsque un Utilisateur est sauvé, on agit sur la table LdapUser pour créer ou mettre à jour l'utilisateur dans le LDAP. 
    @receiver(post_save, sender=Utilisateur)
    def updateLdapUser(sender, instance, **kwargs):
        if instance.is_active:
            if LdapUser.objects.filter(pk_django=instance.pk).count() == 1: #si l'utilisateur existe, mise à jour
                ldapuser_to_modify=LdapUser.objects.get(pk_django=instance.pk)
                ldapuser_to_modify.full_name=instance.username
                ldapuser_to_modify.email=instance.email
                ldapuser_to_modify.first_name=instance.first_name
                ldapuser_to_modify.last_name=instance.last_name
                ldapuser_to_modify.password=instance.ldap_password
                ldapuser_to_modify.save(force_update=True)
            else: #sinon création
                ldapuser_to_save=LdapUser(full_name=instance.username, email=instance.email, first_name=instance.first_name, last_name=instance.last_name, password=instance.ldap_password,pk_django=instance.pk)
                ldapuser_to_save.save()
                manageLdapGroupMember("addmember",instance, instance.groups.all()) #on appelle la méthode pour gérer les groupes à ce niveau pour couvrir l'activation d'un utilisateur existant, précédemment désactivé, qui aurait des groupes
        else:
            if LdapUser.objects.filter(pk_django=str(instance.pk)).count() == 1: #si l'utilisateur n'est pas actif, on le supprime du ldap
                ldapuser_to_delete=LdapUser.objects.get(pk_django=instance.pk)
                ldapuser_to_delete.delete()

    #lorsqu'un Utilisateur est supprimé, on agit sur la table LdapUser pour supprimer l'utilisateur dans le ldap
    @receiver(post_delete, sender=Utilisateur)
    def deleteLdapUser(sender, instance, **kwargs):
        if LdapUser.objects.filter(pk_django=instance.pk).count() == 1:
            ldapuser_to_delete=LdapUser.objects.get(pk_django=instance.pk)
            groups_to_remove=Group.objects.all()
            manageLdapGroupMember("deletemember", instance, groups_to_remove) #comme la suppression d'un utilisateur dans le ldap n'engendre pas automatiquement son appartenance aux groupes, appel de la méthode de gestion des groupes
            ldapuser_to_delete.delete()
 
    #définition d'un modèle pour définir les groupes Ldap
    class LdapGroup(ldapdb.models.Model):
        """
        Class for representing an LDAP group entry.
        """
        # LDAP meta-data
        base_dn = "ou=groups,dc=rezal,dc=fr"
        object_classes = ['groupOfNames']

        # groupOfNames attributes
        name = CharField(db_column='cn', max_length=200, primary_key=True)
        members = ListField(db_column='member', default=['cn=admin,dc=rezal,dc=fr']) #il est obligatoire d'avoir au moins un membre dans un groupe
        pk_django = CharField(db_column='description') #utilisation de la pk django qu'on met dans le champ description

        def __str__(self):
            return self.name

        def __unicode__(self):
            return self.name
    
    #lorsqu'un groupe est sauvé, on met à jour ou on crée le groupe dans le ldap
    @receiver(post_save, sender=Groupe)
    def updateLdapGroup(sender, instance, **kwargs):
        if LdapGroup.objects.filter(pk_django=instance.pk).count() == 1:
            ldapgroup_to_modify=LdapGroup.objects.get(pk_django=instance.pk)
            ldapgroup_to_modify.name=instance.name
            ldapgroup_to_modify.save(force_update=True)
        else:
            ldapgroup_to_save=LdapGroup(name=instance.name, pk_django=instance.pk)
            ldapgroup_to_save.save()

    #lorsqu'un groupe est supprimé, on supprime le groupe dans le ldap
    @receiver(post_delete, sender=Groupe)
    def deleteLdapGroup(sender, instance, **kwargs):
        if LdapGroup.objects.filter(pk_django=instance.pk).count() == 1:
            ldapgroup_to_delete=LdapGroup.objects.get(pk_django=instance.pk)
            ldapgroup_to_delete.delete()

    #lorsque le champ Groupe d'un utilisateur est mis à jour, plusieurs signaux sont envoyé : post_add pour les ajouts, post_delete pour les suppressions. On décide donc de faire un clear complet des groupes dans le ldap puis de faire les mises à jour qui conviennent
    @receiver(m2m_changed, sender=Utilisateur.groups.through)
    def updateLdapGroupMembers(sender, instance, pk_set, action, **kwargs): 
        #clean des groupes dans le ldap
        groups_to_remove=Group.objects.all()
        manageLdapGroupMember("deletemember", instance, groups_to_remove)
        #si l'utilisateur est actif, mise à jour des groupes
        if instance.is_active:
            current_groups=instance.groups.all() #récupération des groupes avant modification
            if action=="post_add": #si on ajoute des groupes
                groups_to_add=Group.objects.filter(pk__in=pk_set)
                groups_to_associate=current_groups.union(groups_to_add) #union des groupes 
                manageLdapGroupMember("addmember", instance, groups_to_associate)
            elif action=="post_remove": #si on retire des groupes
                groups_to_remove=Group.objects.filter(pk__in=pk_set)
                groups_to_associate=current_groups.difference(groups_to_remove) #différence des groupes
                manageLdapGroupMember("addmember", instance, groups_to_associate)                

    def manageLdapGroupMember(action, user, groups):
        ldap_user=LdapUser.objects.get(pk_django=user.pk)
        if action =="addmember":
            for group in groups:
                ldap_group=LdapGroup.objects.get(pk_django=group.pk)
                if ldap_user.dn not in ldap_group.members:
                    ldap_group.members.append(ldap_user.dn)
                    ldap_group.save(force_update=True)
        if action == "deletemember":
            for group in groups:
                ldap_group=LdapGroup.objects.get(pk_django=group.pk)
                if ldap_user.dn in ldap_group.members:
                    ldap_group.members.remove(ldap_user.dn)
                    ldap_group.save(force_update=True)

        
