from django.urls import path

from appcom import views

urlpatterns = [
    path("comgadz/", views.com_gadz, name="comgadz"),
]