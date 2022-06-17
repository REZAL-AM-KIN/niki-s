# -*- coding: utf-8 -*-

from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import Consommateur


# Create your views here.

def has_consommateur(user):
    test=False
    consommateur = Consommateur.objects.filter(consommateur=user)
    if consommateur.count()==1:
        test = True
    return test