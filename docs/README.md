- [Objectifs](#objectifs)
- [Description de la structure de l'application](#description-de-la-structure-de-lapplication)
  - [Appuser](#appuser)
    - [Views](#views)
    - [Models](#models)
    - [Fonctions pertinentes](#fonctions-pertinentes)
  - [Appmacgest](#appmacgest)
    - [Views](#views-1)
    - [Models](#models-1)
  - [Appkfet](#appkfet)
    - [Models](#models-2)
    - [Fonctions pertinentes](#fonctions-pertinentes-1)
    - [Admin](#admin)
  - [Appevents](#appevents)
    - [Views](#views-2)
    - [Models](#models-3)
    - [Fonctions pertinentes](#fonctions-pertinentes-2)
    - [Admin](#admin-1)
- [API](#api)
  - [Installation](#installation)
  - [Conception de l'API](#conception-de-lapi)
    - [Consommateur](#consommateur)
    - [Produit](#produit)
    - [Recharge](#recharge)
    - [Bucquage](#bucquage)
- [Spécifications techniques supplémentaires](#spécifications-techniques-supplémentaires)
  - [Installation](#installation-1)
    - [En dev](#en-dev)
    - [Développer avec VSCode](#développer-avec-vscode)
    - [En prod](#en-prod)
  - [Decorators](#decorators)
  - [Template tags](#template-tags)
  - [Templates](#templates)
  - [LDAP](#ldap)
  - [Mails](#mails)

# Objectifs

- Une seule base de donnée intrakin
- Un front web ([accueil.rezal.fr](http://accueil.rezal.fr)) décrit dans les applications Django comme aujourd'hui en s'appuyant au maximum sur le standard Django
- Un front mobile (KinApp) qui vient taper aec les API Django REST dans les modèles existants
- Un front web ([kfet.rezal.fr](http://kfet.rezal.fr)) avec un design bien approprié (séparé donc de l'intra) qui vient
  taper avec les API Django REST dans les modèles qu'il faut

# Description de la structure de l'application

## Appuser

[Voir la documentation Django](https://docs.djangoproject.com/fr/3.0/topics/auth/customizing/#extending-the-existing-user-model)

L'utilisateur s'inscrit, les attributs ont les statuts suivants par défaut :

- `if_staff`: `false` (accessibilité au site d'administration)
- `is_active`: `true` (défini si l'utilisateur peut se connecter)
- `is_superuser`: `false` (défini si lutilisatreur dispose de tous les droits sans avoir besoin de lui affecter
  spécifiquement)
- `is_gadz`: `false` (défini si l'utilisateur est gadz et peut accéder à des pages spécifiques)
- `is_conscrit`: `false` (défini si l'utilisateur est constrit et peut accéder à des pages spécifiques - permet de
  distinguer les peks notamment)
- `has_cotiz`: `false` (défini si l'utilisateur a payé sa cotiz)
- `date_expiration`: Vide par défaut. Prend la valeur de la date du jour où `has_cotiz` est passé à `true` + 365 jours **A REVOIR**

Un script doit tourner pour passer `has_cotiz` à false lorsque la date du jour dépasse `date_expiration`. **A REVOIR**

### Views

- Index : page d'acceuil
  - Accessible : tout utilisateur authentifié
- About : page "À propos" **A REVOIR**
  - Accessible : tout utilisateur authentifié
- Inscription : page d'inscription
  - Accessible : tout le monde
- LoginPage : page de login
  - Accessible : tout le monde
- GestionCompte : permet de gérer la chambre, le téléphone de contact et si l'utilisateur est gadz, la bucque
  - Accessible : tout utilisateur authentifié
- Administration : permet d'accéder aux différents outils d'administrateur
  - Accessible : utilisateur authentifié ayant le statut équipe
- MdpOublie (standard) **A REVOIR**
  - Accessible : tout le monde
  - Utilisation des vues [Django standards](https://docs.djangoproject.com/fr/3.1/topics/auth/default/#using-the-views) en ajoutant dans le fichier url de l'application les lignes correspondantes. Il sera possible d'ajouter un template
spécifique pour personnaliser ces vues.

L'utilisation de cette fonctionnalité nécessite le paramétrage des mails dans Django.
- Fonctionnalités supplémentaires à implémenter non démarrées :
  - Prévoir un accueil de l'utilisateur en fonction de son statut, type "tutoriel" lors de la première connexion, idéalement en overlay.

### Models

- Utilisateur (dérivé du modèle standard User)
  - La fonction save a été surchargée pour gérer la date d'expiration. **A REVOIR**

### Fonctions pertinentes

- has_cotiz : renvoie `True` si l'utilisateur a sa cotiz payée
- is_superuser : renvoie `True` si l'utilisateur est superuser

## Appmacgest

L'utilisateur peut ajouter ses appareils si `has_cotiz` est `true`. Le premier appareil ajouté dispose d'internet par
défaut (attributs `accepted` et `has_rezal` en `true`). Les autres demandes d'appareil disposent des
attributs `accepted` et `has_rezal` en `false`. Si l'attribut `has_cotiz` de l'utilisateur associé à un appareil est
passé à `false`, l'attribut `has_rezal` de l'appareil passe à `false` et est ainsi retiré de la table radcheck.

Ces changements sont automatiquement faits via une modification de la méthode `save` du user. Pour cela on utilise un receiver associé à la fonction `update_device`.

Un routeur de base de données `Authrouter.py` est utilisé pour communiquer avec la base Radius (table radcheck). C'est dans Radius que pfsense regarde si l'appareil à le droit d'avoir internet.

### Views

- GestionConnexion : permet de visualiser l'ensembe de ses appareils avec leur statut (activé ou désactivé)
  - Accessible : utilisateur authentifié ayant sa cotiz à jour
  - Fonctionnalité supplémentaire à implémenter : possibilité de rajouter un bouton `Supprimer` de la même manière que sur la page `GestionDemandeMac`
- AjoutMac : permet d'ajouter un appareil supplémentaire
  - Accessible : utilisateur authentifié ayant sa cotiz à jour
- GestionDemandeMac : permet de gérer les demandes d'adresses mac
  - Accessible : utilisateur authentifié ayant le statut superuser

### Models

- radcheck - réplication de la table radcheck de la base Radius. Cette table restera toujours vide grâce au routeur de BDD
- Device
  - La fonction save a été surchargée pour interagir avec Radius
  - La fonction delete a été surchargée pour interagir avec Radius
  - Présence d'une REGEX pour vérifier les adresses MAC

## Appkfet

Le modèle `Consommateur` est directement lié à un utilisateur du Rezal (modèle `User`). Il dispose de deux
fonctions `credit` et `debit`, permettant de créditer et débiter le compte de l'utilisateur. Le débit ne fonctionne **
QUE** si l'utilisateur a un solde supérieur ou égal à la valeur débitée.

Il existe un champ permettant de visualiser le cumulé de sa consommation.

L'entité d'un produit dépend des groupes existants dans la solution.

De base, 4 méthodes sont disponibles pour le rechargement: CB, Espèces, Chèque, Lydia.

Chaque bucquage, recharge ou évènement crée une ligne dans la base historique. C'est celle-ci qui sera utilisée par l'API pour retourner l'historique d'un utilisateur.

Fonctionnellement :
- les consommateurs et produits sont créés via l'interface admin Django. Des droits fins seront à mettre en place 
- les recharges, bucquages sont faits uniquement via l'API

### Models

- Consommateurs
- Produits
- Bucquage
- Recharge
- History

### Fonctions pertinentes

- has_consommateur : renvoie `True` si l'utilisateur à un consommateur associé

### Admin

## Appevents

Blabla

### Views

Blabla

### Models

Blabla

### Fonctions pertinentes

Blabla

### Admin

Blabla

# API

## Installation

Utilisation de [Django REST Framework](https://www.django-rest-framework.org/). Utilisation de PyYaml pour générer la
documentation automatiquement

## Conception de l'API

### Consommateur

- `GET`: Récupérer tous les consommateurs

### Produit

- `GET`: Récupérer tous les produits

### Recharge

- `GET`: Récupérer toutes les recharges pour tous les utilisateurs ou un utilisateur donné
- `POST`: Création d'une recharge

La gestion des droits pour créer une recharge sera gérée dans le BO Django directement sur
l'utilisateur: `appkefet | recharge | can add recharge`

### Bucquage

- `GET`: Récupérer tous les bucquages pour tous les utilisateurs ou un utilisateur donné
- `POST`: Créer un bucquage

  La gestion des droits pour créer un bucquage sera gérée dans le BO Django sur le groupe de l'entité.

  Le groupe doit posséder le droit de créer un bucquage: `appkfet | bucquage | can add bucquage`

  Le groupe auquel appartient l'utilisateur lui donne le droit de bucquer les produits de ce groupe

# Spécifications techniques supplémentaires

## Installation

### En dev

Pour tester l'intégralité des fonctionnalités de l'application, à savoir le ldap, il est recommandé de la faire fonctionner sous linux.

`sudo apt-get install git gpg python3 python3-pip ssh python3.10-venv libsasl2-dev libldap2-dev libssl-dev ldap-utils`

En effet, la librairie python permettant d'intéragir avec le LDAP ne fonctionne que sous Linux.

Dans le cas où vous n'avez pas de machine linux sous la main, il est tout à fait possible de désactiver le module LDAP avec le paramètre `WITHLDAP` dans `settings.py`. Il faudra de plus commenter les parties de code qui intègre le module. Il ne sera pas nécessaire d'installer la dernière ligne de requirements.txt qui correspond à une customisation du packet django-ldapdb pour le rézal. 

### Développer avec VSCode

### En prod

Blabla

## Decorators

Ils permettent de restreindre les accès aux pages en fonction des droits et des attributs sur le modèle `User`. A
ajouter juste avant une vue pour limiter son accès. Ils sont cumulables. On retiendra notamment les
décorateurs `@login_required` et `@user_passes_test`.

## Template tags

extra_filters

## Templates

Blabla

## LDAP

Blabla

## Mails

**A REVOIR**
