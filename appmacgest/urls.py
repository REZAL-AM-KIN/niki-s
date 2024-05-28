from django.urls import path

from . import views

urlpatterns = [
    path("gestiondemandemac/", views.gestion_demande_mac, name="gestiondemandemac"),
    path("gestionconnexion/", views.gestion_connexion, name="gestionconnexion"),
    path("ajoutmac/", views.ajout_mac, name="ajoutmac"),
    path("macnotfound/", views.not_logged_in, name="macnotfound"),
    path("activatedevice/<params>", views.activate_device, name="activatedevice"),
    path("deletedevice/<params>", views.delete_device, name="deletedevice"),
    path("disabledevice/<params>", views.disable_device, name="disabledevice"),
]
