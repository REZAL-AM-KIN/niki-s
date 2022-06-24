# -*- coding: utf-8 -*-

from copyreg import dispatch_table
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
import xlwt
import xlrd

# Create your views here.

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
def exportparticipationincsv(request, event):
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
def exportparticipationinxls(request,event):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="participation.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Event')
    
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns =['ID Participation','Username','Nom','Prénom','ID Produit','Produit','Quantité','Participation OK','Participation bucquée']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    query_to_export=Participation_event.objects.filter(product_participation__parent_event=event).values_list('pk', 'cible_participation__consommateur__username', 'cible_participation__consommateur__last_name', 'cible_participation__consommateur__first_name','product_participation__pk', 'product_participation__nom', 'number', 'participation_ok', 'participation_bucquee').order_by('cible_participation__consommateur__last_name')
    for row in query_to_export:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response

@login_required
@user_passes_test(lambda u: u.has_perm('appkfet.can_add_bucquage'))
def listeventstobucque(request):
    list_of_event_to_bucque=Event.objects.filter(ended=False)
    return render(request, "appevents/listeventstobucque.html", {'list':list_of_event_to_bucque})

@login_required
@user_passes_test(lambda u: u.has_perm('appkfet.can_add_bucquage'))
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
    book = xlrd.open_workbook(file_contents = file.read(), encoding_override = 'utf-8')
    sheet = book.sheet_by_name("Event")
    row_count = sheet.nrows
    col_count = sheet.ncols
    for cur_row in range(1, row_count):
        id_participation=sheet.cell(cur_row,0).value
        username=sheet.cell(cur_row,1).value
        id_produit=sheet.cell(cur_row,4).value
        quantity=sheet.cell(cur_row,6).value
        participation_ok=sheet.cell(cur_row,7).value
        participation_bucquee=sheet.cell(cur_row,8).value
        if id_participation != '':
            if Participation_event.objects.filter(pk=id_participation).count()==1: #si la participation existe
                targetparticipation=Participation_event.objects.get(pk=id_participation)
                if participation_ok==1 and participation_bucquee==0: #si la participation est validée et non bucquée
                    if id_produit == targetparticipation.product_participation.pk: #si le produit renseigné dans le fichier est le même que celui enregistré en base
                        if username == targetparticipation.cible_participation.consommateur.username: #si le consommateur renseigné dans le fichier est le même que celui enregistré en base
                            targetparticipation.participation_ok=True #passage à True dans l'instance du modèle
                            targetparticipation.number=quantity #application de la bonne quantité
                            targetparticipation.save() #sauvegarde et bucquage via la méthode du modèle
                        else:
                            error=+1
                    else:
                        error=+1
                else:
                    error=+1
            else:
                error=+1
        else: #si la participation n'existe pas (la première case est vide)
            if Consommateur.objects.filter(consommateur__username=username).count()==1:
                cible_participation=Consommateur.objects.get(consommateur__username=username)
            else:
                error=+1
            if Product_event.objects.filter(pk=id_produit).count()==1:
                product_participation=Product_event.objects.get(pk=id_produit)
                if product_participation.parent_event==event:
                    if participation_ok==1:
                        participation_ok=True
                    else:
                        participation_ok=False
                    Participation_event.objects.get_or_create(cible_participation=cible_participation,product_participation=product_participation,number=quantity,participation_ok=participation_ok)
                else:
                    error=+1
            else:
                error=+1
    return error