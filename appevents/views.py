# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render
from appevents.models import Event, Product_event, Participation_event
from appkfet.views import has_consommateur
from .forms import BucqueEventForm, ParticipationEventForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from appkfet.models import Consommateur
import csv
import re

# Create your views here.

#Permet de lister l'ensemble des évènements encore ouverts à l'inscription. Si l'utilisateur est déjà inscrit à l'évènement alors, la page d'inscription n'est pas disponible
#Pour accéder à cette page il est nécessaire d'avoir un compte kfet (Consommateur)
@login_required
@user_passes_test(has_consommateur)
def listevents(request):
    list_of_event_subscribed = []
    list_to_display=Event.objects.filter(Q(cansubscribe=True))
    consommateur=Consommateur.objects.get(consommateur=request.user)
    participation_event_subscribed_list=Participation_event.objects.filter(cible_participation=consommateur)
    for participation_subscribed in participation_event_subscribed_list:
        product_event_subscribed=participation_subscribed.product_participation
        event_subscribed=product_event_subscribed.parent_event
        list_of_event_subscribed.append(event_subscribed)   
    return render(request, "appevents/listevents.html", {"list": list_to_display, "subscribed":list_of_event_subscribed})

#Il s'agit uniquement d'une page de redirection vers les formulaires d'inscription de chaque produit de l'évènement
#Ces URLs pourront apparaitre directement sur Facebook
#Pour accéder à cette page il est nécessaire d'avoir un compte kfet (Consommateur)
#Params désigne l'ID de l'évènement auquel on souhaite s'inscrire
#Step est initialisé à 0. Sa valeur maximale est égale au nombre de produits présents dans l'évènement
@login_required
@user_passes_test(has_consommateur)
def subevent(request, params, step):
    event_to_subscribe = Event.objects.get(pk=params)
    if event_to_subscribe.cansubscribe == False:
        messages.error(request, u"Les inscriptions à cet évènement sont fermées")
        return redirect(listevents)
    product_list_to_choose = Product_event.objects.filter(parent_event=event_to_subscribe)
    step=int(step)
    while step < len(product_list_to_choose):
        product_to_sub=product_list_to_choose[step].pk
        return redirect(subproductevent, step=step, product_to_sub=product_to_sub)
    messages.success(request, u"Inscription finalisée")
    return redirect(listevents)

#Pour accéder à cette page il est nécessaire d'avoir un compte kfet (Consommateur)
#Step est passé ici pour être renvoyé ensuite à la page de redirection en l'incrémentant
#Product_to_sub est l'ID du produit de l'évènement sur lequel s'inscrire
#Un contrôle est fait sur la valeur de la quantité qui doit être positive ou nulle
@login_required
@user_passes_test(has_consommateur)
def subproductevent(request, step, product_to_sub):
    product_to_sub_instance=Product_event.objects.get(pk=product_to_sub)
    if request.method=="POST":
        form=ParticipationEventForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data["number"]
            if number < 0:
                messages.error(request, u"Une erreur est survenue lors de l'inscription")
                return redirect(listevents)
            if number > 0:
                cible_participation = Consommateur.objects.get(consommateur=request.user)
                participation=Participation_event(number=number, product_participation=product_to_sub_instance, cible_participation=cible_participation)
                participation.save()
            if number == 0 and product_to_sub_instance.obligatoire==True:
                messages.warning(request, u"Ce produit est obligatoire")
                return redirect(subproductevent, step=step, product_to_sub=product_to_sub)
            step = int(step) + 1
            return redirect(subevent, params=product_to_sub_instance.parent_event.pk,step=step)                
        else:
            messages.error(request, u"Une erreur est survenue lors de l'inscription")
            return redirect(listevents)
    else:
        form=ParticipationEventForm()
        return render(request, "appevents/event.html", {"form": form, "step":step, "product_to_sub_instance":product_to_sub_instance})

@login_required
def exportparticipation(request, event):
    output=[]
    response=HttpResponse(content_type='text/csv')
    response.write(u'\ufeff'.encode('utf8'))
    writer=csv.writer(response)
    query_to_export=Participation_event.objects.filter(product_participation__parent_event=event)
    writer.writerow(['ID Participation','Username','Nom','Prénom','ID Produit','Produit','Quantité','Participation OK','Participation bucquée'])
    for line in query_to_export:
        output.append([line.pk, line.cible_participation.consommateur.username, line.cible_participation.consommateur.last_name, line.cible_participation.consommateur.first_name, line.product_participation.pk, line.product_participation.nom, line.number, line.participation_ok, line.participation_bucquee])
    writer.writerows(output)
    return response

@login_required
@user_passes_test(lambda u: u.has_perm('appkfet.can_add_event'))
def listeventstobucque(request):
    list_of_event_to_bucque=Event.objects.filter(ended=False)
    return render(request, "appevents/listeventstobucque.html", {'list':list_of_event_to_bucque})

@login_required
def eventtobucque(request, event):
    if request.method=="POST":
        form=BucqueEventForm(request.POST, request.FILES)
        if form.is_valid():
            error=manageparticipationfile(request.FILES['file'],event)
            if error == 0:
                messages.success(request, u"Bucquage réalisé sans erreur, téléchargez le rapport ici")
            else:
                messages.warning(request, u"Bucquage réalisé avec erreur(s), téléchargez le rapport ici")
            return redirect(listeventstobucque)
    else:
        form=BucqueEventForm()
    return render(request, "appevents/eventtobucque.html", {'form':form, 'event':event})
    
def manageparticipationfile(file,event):
    error=0
    file_data = file.read().decode("utf-8-sig")
    rows = file_data.split("\r\n")
    for row in rows: #pour chaque ligne du fichier
        row=re.split(r"\s*[,;]\s*", row.strip())
        patate=row[0]
        if row[0] != 'ID Participation': #on saute la première ligne de headers
            if Participation_event.objects.filter(pk=row[0]).count()==1: #si la participation existe
                targetparticipation=Participation_event.objects.get(pk=row[0])
                if row[7]==True and row[8]==False: #si la participation est validée et non bucquée
                    if row[4] == targetparticipation.product_event.pk: #si le produit renseigné dans le fichier est le même que celui enregistré en base
                        if row[1] == targetparticipation.cible_participation.username: #si le consommateur renseigné dans le fichier est le même que celui enregistré en base
                            targetparticipation.participation_ok=True #passage à True dans l'instance du modèle
                            targetparticipation.number=row[5] #application de la bonne quantité
                            targetparticipation.save() #sauvegarde et bucquage via la méthode du modèle
                        else:
                            error=+1
                    else:
                        error=+1
                else:
                    error=+1
            else: #si la participation n'existe pas (la première case est vide)
                if Consommateur.objects.filter(username=row[1]).count()==1:
                    cible_participation=Consommateur.objects.get(username=row[1])
                else:
                    error=+1
                if Product_event.objects.filter(pk=row[4]).count()==1:
                    product_participation=Product_event.objects.get(pk=row[4])
                    if product_participation.parent_event==event:
                        Participation_event.objects.get_or_create(cible_participation=cible_participation,product_participation=product_participation,number=row[5],participation_ok=row[7])
                    else:
                        error=+1
                else:
                    error=+1
    return error