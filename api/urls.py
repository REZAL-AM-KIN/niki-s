from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"permissions", views.PermissionsViewSet, basename="permissions")
router.register(r"utilisateur", views.CurrentUserViewSet, basename="utilisateur")
router.register(r"produits", views.ProduitViewSet)
router.register(r"entites", views.EntiteViewSet)
router.register(r"consommateurs", views.ConsommateurViewSet)
router.register(r"recharges", views.RechargeViewSet, basename="recharges")
router.register(r"bucquages", views.BucquageViewSet, basename="bucquages")
router.register(r"history", views.HistoryViewSet, basename="history")
router.register(r"rechargeslydia", views.RechargeLydiaViewSet, basename="rechargeslydia")
router.register(r"event", views.EventViewSet, basename="event")
router.register(r"productevent", views.ProductEventViewSet, basename="productevent")
router.register(r"bucquagevent", views.BucqageEventViewSet, basename="bucqagevent")

urlpatterns = [
    path("", include(router.urls)),
]
