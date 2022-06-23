# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("listevents/", views.listevents, name="listevents"),
    path("subevent/<params>/<step>", views.subevent, name="subevent"),
    path("subproductevent/<step>/<product_to_sub>", views.subproductevent, name="subproductevent"),
    path("exportparticipationincsv/<event>", views.exportparticipationincsv, name="exportparticipationincsv"),
    path("exportparticipationinxls/<event>", views.exportparticipationinxls, name="exportparticipationinxls"),
    path("listeventstobucque", views.listeventstobucque, name="listeventstobucque"),
    path("eventtobucque/<event>", views.eventtobucque, name="eventtobucque")
]
