from django.urls import path

from . import views

urlpatterns = [
    path("gestiondemandemac/", views.gestion_demande_mac, name="gestiondemandemac"),
    path("gestionconnexion/", views.gestion_connexion, name="gestionconnexion"),
    path("ajoutmac/", views.ajout_mac, name="ajoutmac"),
    path("activatedevice/<params>", views.activate_device, name="activatedevice"),
    path("deletedevice/<params>", views.delete_device, name="deletedevice"),
]
