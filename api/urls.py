# -*- coding: utf-8 -*-

from rest_framework import routers
from django.urls import path, include

from . import views

router = routers.DefaultRouter()
router.register(r"produits", views.ProduitViewSet)
router.register(r"consommateurs", views.ConsommateurViewSet)
router.register(r"recharges", views.RechargeViewSet, basename="recharges")
router.register(r"bucquages", views.BucquageViewSet, basename="bucquages")
# router.register(r"transactions",views.TransactionViewSet, basename="transaction")
router.register(r"history", views.HistoryViewSet, basename="history")

urlpatterns = [
    path('', include(router.urls)),
]