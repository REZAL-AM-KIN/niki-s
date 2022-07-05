- [Objectifs](#objectifs)
- [Description de la structure de l'application](#description-de-la-structure-de-lapplication)
  - [Appuser](#appuser)
    - [Views](#views)
    - [Models](#models)
    - [Fonctions pertinentes](#fonctions-pertinentes)
    - [Admin](#admin)
  - [Appmacgest](#appmacgest)
    - [Views](#views-1)
    - [Models](#models-1)
  - [Appkfet](#appkfet)
    - [Models](#models-2)
    - [Fonctions pertinentes](#fonctions-pertinentes-1)
    - [Admin](#admin-1)
  - [Appevents](#appevents)
    - [Views](#views-2)
    - [Models](#models-3)
    - [Fonctions pertinentes](#fonctions-pertinentes-2)
    - [Admin](#admin-2)
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
    - [Reset migrations](#reset-migrations)
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
- `ldap_password`: correspond au mot de passe hashé envoyé au ldap

Un script doit tourner pour passer `has_cotiz` à false lorsque la date du jour dépasse `date_expiration`. **A REVOIR**

Rappel : un utilisateur ne doit pas être supprimé directement. Il doit être désactivé, conservé un certain temps (1 an) après sa désactivation pour des soucis d'Hadopi, puis il pourra être supprimé. Dans le cas où l'utilisateur était supprimé directement sans être passé par `is_active=False`, il ne sera pas retiré du LDAP. Il serait pertinent de surcharger la méthode delete du modèle user pour y rajouter la suppression de l'entrée LDAP.

### Views

- Index : page d'acceuil
  - Accessible : tout utilisateur authentifié
- About : page "À propos" **A REVOIR**
  - Accessible : tout utilisateur authentifié
- Inscription : page d'inscription
  - Accessible : tout le monde
  - Un Captcha est utilisé - utilisation de l'app standard django simple captcha
- LoginPage : page de login
  - Accessible : tout le monde
- GestionCompte : permet de gérer la chambre, le téléphone de contact et si l'utilisateur est gadz, la bucque
  - Accessible : tout utilisateur authentifié
- Administration : permet d'accéder aux différents outils d'administrateur
  - Accessible : utilisateur authentifié ayant le statut équipe
- MdpOublie (standard) **A REVOIR**
  - Accessible : tout le monde
  - Utilisation des vues [Django standards](https://docs.djangoproject.com/fr/3.1/topics/auth/default/#using-the-views) en ajoutant dans le fichier url de l'application les lignes correspondantes. Il sera possible d'ajouter un template
spécifique pour personnaliser ces vues. L'utilisation de cette fonctionnalité nécessite le paramétrage des mails dans Django.
- Fonctionnalités supplémentaires à implémenter non démarrées :
  - Prévoir un accueil de l'utilisateur en fonction de son statut, type "tutoriel" lors de la première connexion, idéalement en overlay. Une ébauche de cette fonctionnalité a été développée dans une des versions précédentes de l'intra. **A REVOIR**

### Models

- Utilisateur (dérivé du modèle standard User)
  - La fonction save a été surchargée pour gérer la date d'expiration. **A REVOIR**
  - La fonction save a été surchargée pour gérer le ldap et créer, mettre à jour ou supprimer l'entrée côté LDAP. Si l'utilisateur est passé en `is_active=False`, l'entrée est immédiatement supprimée côté LDAP
  - La fonction set_password permet de hasher le mot de passe rentré par l'utilisateur selon l'algorithme utilisé par le LDAP (SSHA). Ce mot de passe hashé est stocké dans l'attribut `ldap_password`

### Fonctions pertinentes

- has_cotiz : renvoie `True` si l'utilisateur a sa cotiz payée
- is_superuser : renvoie `True` si l'utilisateur est superuser

### Admin

La table User a été unregister de l'interface. Elle ne doit jamais être utilisée puisque ce modèle est surchargé par Utilisateur. 
Pour supprimer le premier utilisateur créé lors de l'installation de l'application (qui est un User et non un Utilisateur), il est possible de décommenter cette ligne, se connecter avec le superutilisateur et supprimer ce compte.

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
fonctions `credit` et `debit`, permettant de créditer et débiter le compte de l'utilisateur. Le débit ne fonctionne **QUE** si l'utilisateur a un solde supérieur ou égal à la valeur débitée.

Il existe un champ permettant de visualiser le cumulé de sa consommation.

L'entité d'un produit dépend des groupes existants dans la solution.

De base, 4 méthodes sont disponibles pour le rechargement: CB, Espèces, Chèque, Lydia.

Chaque bucquage ou recharge crée une ligne dans la base historique. C'est celle-ci qui sera utilisée par l'API pour retourner l'historique d'un utilisateur.

Fonctionnellement :
- les consommateurs et produits sont créés via l'interface admin Django. Des droits fins seront à mettre en place 
- les recharges, bucquages, visualisation de l'historique sont faits uniquement via l'API qui devra être appelée par un front

### Models

- Consommateurs
  - Trois fonctions rattachées à ce modèle : 
    - credit qui ajoute de l'argent sur le solde du consommateur
    - debit qui retire de l'argent sur le solde du consommateur. Ne teste pas si le solde est positif à la suite du débit !
    - testdebit qui permet de savoir si le solde sera positif après le débit.
- Produits
- Bucquage
  - La méthode save est surchargée pour mettre à jour le solde du consommateur. Si la fonction testdebit renvoie True, alors la fonction debit est appelée et la ligne d'History rajoutée. 
- Recharge
  - Quatre méthodes de recharge écrites en dur dans le modèle. C'est ici qu'il faudra toucher si besoin et cela se répartira dans les autres applis
  - La méthode save est surchargée pour mettre à jour le solde du consommateur (en appelant la fonction credit). Une ligne est également ajoutée dans la table History
- History

### Fonctions pertinentes

- has_consommateur : renvoie `True` si l'utilisateur à un consommateur associé

### Admin

Comme vu précédemment, les consommateurs et produits sont créés via l'interface admin Django. Pour que le fonctionnel corresponde à nos besoins, certaines fonctions ont été surchargées dans `admin.py`. Hors superuser (qui peut tout faire !), les règles sont les suivantes : 
- Il n'est possible de modifier un produit que si l'utilisateur dispose de la permission change_produit ET qu'il fait parti de l'entité du produit créé. Ce test est fait en surchargeant la méthode "has_change_permission"
- Il est possible de créer un produit relié à une entité UNIQUEMENT si on y appartient. Ce test est fait à la surcharge de la méthode save. 

**A REVOIR** Il serait pertinent de modifier la dropdown de choix d'entité lors de la création d'un produit pour n'afficher que les entités où j'ai les droits. De la même manière, la création d'un consommateur ne doit proposer dans la liste déroulante que des utilisateurs qui n'ont pas déjà de consommateur associé et qui sont `is_active==True` **A REVOIR**

Les tables Bucquage, Recharge, History ne sont pas disponibles dans l'interface admin (admin.site.register est commenté) car il serait trop facile de tricher ou de faire une erreur !

## Appevents

Cette application a pour but de gérer les évènements organisés à KIN et surtout les fin's. L'objectif est de créer des évènements (Event), composés de produits (Product_Event) obligatoires ou non et que les utilisateurs (Consommateur) puissent s'y inscrire (Participation_Event). Un évènement peut être ouvert à l'inscription ou pas, terminé ou pas.
La liste des évènements peut être consultable sur l'interface de la solution. Il sera aussi possible de générer le lien d'inscription, de le poster sur un groupe Facebook pour que les gens puissent s'inscrire directement.
La solution proposera ensuite une interface permettant d'exporter les participations. Cet export permettra de valider les présents, d'en rajouter ou d'en supprimer. Le fichier modifié sera réimporté dans la solution qui validera ou non les bucquages.

Fonctionnellement :
- la création des évènements et des produits de ces évènements est faite via l'interface admin de django. Lorsqu'un évènement est terminé il est passé à "ended"=False par son créateur ou un administrateur. Cette partie n'est accessible qu'au groupe "Event Manager" (par exemple) qui dispose des permissions create_event, change_event, create_product_event, change_product_event, delete_product_event
- l'inscription et le bucquage sont faits via la solution.

### Views

- listevents
  - Accessible : tous les utilisateurs connectés ayant un Consommateur associé
  - Permet de lister l'ensemble des évènements encore ouverts à l'inscription. La liste des évènements auxquels l'utilisateur est déjà inscrit est également transmise afin de gérer l'affichage (si inscrit : pas d'affichage du bouton inscrire, si pas inscrit : affichage)
- subevent
  - Accessible : tous les utilisateurs connectés ayant un Consommateur associé
  - Vue de redirection vers les formulaires d'inscription de chaque produit de l'évènement. C'est l'URL de cette page, avec la step à 0 qui pourra être partagée sur Facebook.
  - Fonctionnalité supplémentaire à implémenter : 
    - Peut-on vouloir autoriser le bucquage uniquement si le solde du consommateur est supérieur ou égal au coût de l'évènement ?
    - Il serait pertinent de rajouter un contrôle ici pour s'assurer que l'utilisateur ne se réinscrit pas. Le bouton d'inscription ne sera certes pas disponible mais un petit malin pourrait taper directement l'URL.
- subproductevent
  - Accessible : tous les utilisateurs connectés ayant un Consommateur associé.
  - Vue présentant un formulaire pour chaque produit de l'évènement
  - Fonctionnalité supplémentaire à implémenter : il serait pertinent de rajouter un contrôle ici pour s'assurer que l'utilisateur ne se réinscrit pas. Le bouton d'inscription ne sera certes pas disponible mais un petit malin pourrait taper directement l'URL.
- Fonctionnalité supplémentaire à implémenter : la modification ou l'annulation de l'inscription à l'évènement pour un utilisateur
- exportparticipationincsv (deprecated - on utilise xls car c'est plus simple !)
  - Accessible : tous les utilisateurs connectés
- exportparticipationinxls
  - Accessible : tous les utilisateurs connectés
  - Utilisation de la librairie xlwt (Excel writer)
- listeventstobucque
  - Accessible : tous les utilisateurs ayant la permission "can_add_bucquage". A voir si besoin d'affiner
  - Affiche tous les évènements qui sont en "ended=False".
- eventtobucque
  - Accessible : tous les utilisateurs ayant la permission "can_add_bucquage". A voir si besoin d'affiner
  - Permet de charger le fichier exporté et modifié avec les participations
  - Fonctionnalités supplémentaires à implémenter : 
    - Faire apparaitre le nombre d'erreur dans le message passé à la suite de la validation de l'import
    - Sortir un rapport à la suite de l'import. Dans la solution actuelle, il suffit de réexporter les participations de l'évènement et de regarder ce qui a marché ou pas (en cherchant...)! Une solution temporaire pourrait être de rajouter dans l'export une colonne commentaire qui décrirait ce qui s'est bien passé (ou pas) sur chaque ligne. 

### Models

- Event
- Product_event
- Participation_event
  - Surcharge de la méthode save. C'est ici que le débit du solde du consommateur est effectué (après testdebit). Une ligne est rajoutée dans la table History.

### Fonctions pertinentes

manageparticipationfile : permet de lire le fichier importé avec les participations et de réaliser les modifications dans la base de données. 
**A REVOIR** il manque peut être quelques contrôles mais le gros du fonctionnement est OK

### Admin

Pour cette application, les objets Event et Product Event sont créés directement dans l'interface d'administration. Pour que le fonctionnel corresponde à nos besoins, certaines fonctions ont été surchargées dans `admin.py`. Hors superuser (qui peut tout faire !), les règles sont les suivantes : 
- il est nécessaire d'avoir le groupe Event manager qui contient les bonnes permissions (cité plus haut)
- Evènement :
  - Lors de la création d'un Event, le champ "created_by" est rempli avec la FK de l'utilisateur. La distinction création/modification est automatiquement détectée par django admin avec la variable change
  - Je peux voir/changer uniquement les évènements que j'ai créé
  - Il n'est pas possible de supprimer un évènement
- Produit Evènement :
  - Je ne peux créer/voir/changer que des produits sur les évènements que j'ai créé
  - Il n'est pas possible de suppriemr un produit
  - Fonctionnalité supplémentaire à développer : dans la dropdown de création de produit, ne proposer que les évènements que j'ai créé qui sont à ended=False (et pas tous comme aujourd'hui)
- Participation Evènement : non accessible dans l'interface d'admin. Il serait trop facile de tricher ou de faire une erreur !

# API

## Installation

- Utilisation de [Django REST Framework](https://www.django-rest-framework.org/). 
- Utilisation de PyYaml et uritemplates pour générer la documentation automatiquement, accessible sur api-docs
- Utilisation de [Django Rest Framework Simple JWT](https://simpleisbetterthancomplex.com/tutorial/2018/12/19/how-to-use-jwt-authentication-with-django-rest-framework.html) pour authentifier les endpoints en production. L'authentification "SessionAuthentication" est conservée pour pouvoir utiliser la browsable API proposée par Django

## Conception de l'API

- Pagination : utilisation du modèle de pagination standard [Limitoffsetpagination](https://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination). Ajout d'un paramètre dans settings.py. Les pages font 25 occurences.

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

Pour tester l'intégralité des fonctionnalités de l'application, à savoir le ldap, il est recommandé de la faire fonctionner sous linux. En effet, la librairie python permettant d'intéragir avec le LDAP ne fonctionne que sous Linux.

Paquets à installer sur la machine :

`sudo apt-get install git gpg python3 python3-pip ssh libsasl2-dev libldap2-dev libssl-dev ldap-utils libz-dev libjpeg-dev libfreetype6-dev python-dev`

Si vous souhaitez installer le LDAP en local, c'est à ce moment. Voir section LDAP plus bas.

Téléchargement de l'application via le github en ayant préalablement enregistré sa [clé SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

Création d'un fichier .env à la racine du projet en duplicant le fichier .env-template. Ce fichier .env permet de rentrer les informations suivantes :
- SECRET_KEY=!k#$kliodbhcw1wfardw9ua5241c+-_csaao&sv_x2)70*xxf& - à changer pour la production
- DEBUG=True - à mettre à False en production
- LOCALDB=True - permet de définir si on utilise la base de données interne sqlite. Si le paramètre n'est pas à True, il est nécessaire de remplir les informations de connexion à la base de données externe
- RADIUS=False - permet de définir si on doit se connecter à Radius. Si le paramètre n'est pas à False, il est nécessaire de remplir les informations de connexion à la base Radius
- Connexion à la base de données externe : DB_NAME, DB_USERNAME, DB_PASSWORD, DB_ADDR
- Connexion au LDAP : LDAP_ADDR, LDAP_USER, LDAP_PASSWORD
- Connexion à Radius : RADIUS_USERNAME, RADIUS_PASSWORD, RADIUS_ADDR

Lancement de l'application : 

`pip install -r requirements.txt` - si vous choisissez d'installer l'application sans LDAP, utiliser `pip install -r requirements-noldap.txt`

`python3 manage.py makemigrations`

`python3 manage.py migrate`

`python3 manage.py createsuperuser`

`python3 manage.py runserver 0.0.0.0:8000`


Il est nécessaire de vérifier que les login du serveur LDAP local sont corrects (dans `niki/settings.py`).

Une fois les commandes lancées avec succès, il est possible se connecter sur http://ipdelamachine:8000. 
Arrivé sur la page d'accueil, créer un utilisateur via le formulaire d'inscription. Se connecter ensuite avec le compte admin créé au dessus et configurer le nouveau compte pour être superuser et staff. Il ne faudra plus se connecter avec le compte admin par la suite. En effet, le compte admin n'est que instance du modèle User et pas du modèle Utilisateur dérivé.

### Développer avec VSCode

### Reset migrations

`git reset --hard origin/main` : supprime tous ses changements locaux et de récupérer la branche distante

`rm -rf db.sqlite3` : supprime la base de donnée locale

`find . -path "*/migrations/*.py" -not -name "__init__.py" -delete` : supprime les fichiers de migrations

`find . -path "*/migrations/*.pyc"  -delete` : supprime les fichiers de migrations

### En prod

Blabla

## Decorators

Ils permettent de restreindre les accès aux pages en fonction des droits et des attributs sur le modèle `User`. A
ajouter juste avant une vue pour limiter son accès. Ils sont cumulables. On retiendra notamment les
décorateurs `@login_required` et `@user_passes_test`.

## Template tags

extra_filters

## Templates

Le dossier des templates est stocké à la racine de l'application. Il est nécessaire qu'il soit rangé :
- templates
  - templates généraux utilisés par toutes les applications
  - myapp/
    - templates de chaque applications

Dans la solution, nous avons deux types d'architectures : la page d'accueil et les bases d'interfaces et de formulaires. On a donc :

- base.html : contient les appels CSS/js et les liens footers
  - block title : contient le titre écrit dans l'onglet
  - navbar.html
    - Le menu fixe en haut : 
      - mainlinks.html
        - Liens communs
        - Si l'utilisateur a un consommateur activé : lien vers les évènements
      - Si l'utilisateur est gadz : navbar_gadz.html
      - Si l'utilisateur conscrit : navbar_conscrit.html
      - Si l'utilisateur est staff : navbar_staff.html
      - Le bouton de déconnexion
    - Le menu responsive pour le mode mobile (réduit à gauche)
      - mainlinks.html
        - Liens communs
        - Si l'utilisateur a un consommateur activé : lien vers les évènements
      - Si l'utilisateur est gadz : navbar_gadz.html
      - Si l'utilisateur conscrit : navbar_conscrit.html
      - Si l'utilisateur est staff : navbar_staff.html
      - Le bouton de déconnexion
  - block content : contient le corps de la page
    - Pour la page d'index, le menu "descendant" est de nouveau répété dans ce block.
- baseform.html : contient les appels CSS/js et messages envoyés par les vues
  - block title
  - block navform
    - Lien vers l'accueil
    - block formlinks
  - Messages
  - block content

## LDAP

Il est possible d'installer un serveur LDAP sur sa propre machine de test. Pour cela :
- Définir l'host de sa machine en 
  - éditant le fichier /etc/hosts et en ajoutant la ligne : `172.20.0.171 ldap.example.com`
  - exécutant cette commande : `sudo hostnamectl set-hostname ldap.example.com --static`
- Installer le paquet correspondant au serveur LDAP : `slapd`
- Définir un mot de passe administrateur pour le serveur
- Définir le schéma et le premier utilisateur : `sudo ldapadd -x -D cn=admin,dc=example,dc=com -W -f basedn.ldif`. Le fichier basedn.ldif est disponible dans le répertoire docs de ce repository
  
## Mails

**A REVOIR**
