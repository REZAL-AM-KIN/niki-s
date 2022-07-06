# -*- coding: utf-8 -*-

from django.core import exceptions
from appkfet.models import Consommateur

from appuser.models import Utilisateur


def getUtilisateur(request):
    try:
        utilisateur = Utilisateur.objects.get(pk=request.user.pk)
    except:
        utilisateur = None
    return {"utilisateur": utilisateur}

def getConsommateur(request):
    if request.user.is_authenticated:
        try:
            consommateur = Consommateur.objects.get(consommateur=request.user)
        except:
            consommateur = None
        return {"consommateur": consommateur}
    return {}