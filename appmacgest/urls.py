# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("gestiondemandemac/", views.gestiondemandemac, name="gestiondemandemac"),
    path("gestionconnexion/", views.gestionconnexion, name="gestionconnexion"),
    path("ajoutmac/", views.ajoutmac, name="ajoutmac"),
    path("activatedevice/<params>", views.activatedevice, name="activatedevice"),
    path("deletedevice/<params>", views.deletedevice, name="deletedevice"),
]
