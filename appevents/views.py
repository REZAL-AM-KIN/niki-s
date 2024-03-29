import csv
import os
from decimal import Decimal

import xlrd
import xlwt
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from xlutils.copy import copy

from appevents.models import Event, ProductEvent, ParticipationEvent
from appkfet.models import Consommateur
from appkfet.views import has_consommateur
from niki.settings import MEDIA_ROOT
from .forms import BucqueEventForm, ParticipationEventForm


@login_required
@user_passes_test(has_consommateur)
def list_events(request):
    list_of_event_subscribed = []
    list_to_display = Event.objects.filter(Q(can_subscribe=True) & Q(ended=False))
    consommateur = Consommateur.objects.get(consommateur=request.user)
    participation_event_subscribed_list = ParticipationEvent.objects.filter(
        cible_participation=consommateur
    )
    for participation_subscribed in participation_event_subscribed_list:
        product_event_subscribed = participation_subscribed.product_participation
        event_subscribed = product_event_subscribed.parent_event
        list_of_event_subscribed.append(event_subscribed)
    return render(
        request,
        "appevents/listevents.html",
        {"list": list_to_display, "subscribed": list_of_event_subscribed},
    )


# Params désigne l'ID de l'évènement auquel on souhaite s'inscrire
# Step est initialisé à 0. Sa valeur maximale est égale au nombre de produits présents dans l'évènement
@login_required
@user_passes_test(has_consommateur)
def sub_event(request, params, step):
    event_to_subscribe = Event.objects.get(pk=params)
    if event_to_subscribe.can_subscribe is False:
        messages.error(request, "Les inscriptions à cet évènement sont fermées")
        return redirect(list_events)
    product_list_to_choose = ProductEvent.objects.filter(
        parent_event=event_to_subscribe
    )
    step = int(step)
    while step < len(product_list_to_choose):
        product_to_sub = product_list_to_choose[step].pk
        return redirect(sub_product_event, step=step, product_to_sub=product_to_sub)
    messages.success(request, "Inscription finalisée")
    return redirect(list_events)


# Step est passé ici pour être renvoyé ensuite à la page de redirection en l'incrémentant
# Product_to_sub est l'ID du produit de l'évènement sur lequel s'inscrire
# Un contrôle est fait sur la valeur de la quantité qui doit être positive ou nulle
@login_required
@user_passes_test(has_consommateur)
def sub_product_event(request, finss):
    products = ProductEvent.objects.filter(parent_event__pk=finss)
    if request.method == "POST":
        messages.warning(request, "Post")
        return redirect(
                     sub_product_event, finss=finss
                 )
        # form = ParticipationEventForm(request.POST)
        # if form.is_valid():
        #     number = form.cleaned_data["number"]
        #     if number < 0:
        #         messages.error(request, "Une erreur est survenue lors de l'inscription")
        #         return redirect(list_events)
        #     if number > 0:
        #         cible_participation = Consommateur.objects.get(
        #             consommateur=request.user
        #         )
        #         participation = ParticipationEvent(
        #             number=number,
        #             product_participation=product_to_sub_instance,
        #             cible_participation=cible_participation,
        #         )
        #         participation.save()
        #     if number == 0 and product_to_sub_instance.obligatoire is True:
        #         messages.warning(request, "Ce produit est obligatoire")
        #         return redirect(
        #             sub_product_event, step=step, product_to_sub=product_to_sub
        #         )
        #     step = int(step) + 1
        #     return redirect(
        #         sub_event, params=product_to_sub_instance.parent_event.pk, step=step
        #     )
        # else:
        #     messages.error(request, "Une erreur est survenue lors de l'inscription")
        #     return redirect(list_events)
    else:
        form = ParticipationEventForm(products)
        return render(
            request,
            "appevents/event.html",
            {
                "form": form,
                "products": products,
                "finss": finss
            },
        )


@login_required
def export_participation_in_csv(request, event):
    output = []
    response = HttpResponse(content_type="text/csv")
    response.write("\ufeff".encode("utf8"))
    writer = csv.writer(response)
    query_to_export = ParticipationEvent.objects.filter(
        product_participation__parent_event=event
    )
    writer.writerow(
        [
            "ID Participation",
            "Username",
            "Nom",
            "Prénom",
            "ID Produit",
            "Produit",
            "Quantité",
            "Participation OK",
            "Participation bucquée",
        ]
    )
    for line in query_to_export:
        output.append(
            [
                line.pk,
                line.cible_participation.consommateur.username,
                line.cible_participation.consommateur.last_name,
                line.cible_participation.consommateur.first_name,
                line.product_participation.pk,
                line.product_participation.nom,
                line.number,
                line.participation_ok,
                line.participation_bucquee,
            ]
        )
    writer.writerows(output)
    return response


@login_required
def export_participation_in_xls(request, event):
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="participation.xls"'
    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Event")

    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = [
        "ID Participation",
        "Username",
        "Nom",
        "Prénom",
        "ID Produit",
        "Produit",
        "Quantité",
        "Participation OK",
        "Participation bucquée",
    ]
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    query_to_export = (
        ParticipationEvent.objects.filter(product_participation__parent_event=event)
        .values_list(
            "pk",
            "cible_participation__consommateur__username",
            "cible_participation__consommateur__last_name",
            "cible_participation__consommateur__first_name",
            "product_participation__pk",
            "product_participation__nom",
            "number",
            "participation_ok",
            "participation_bucquee",
        )
        .order_by("cible_participation__consommateur__last_name")
    )
    for row in query_to_export:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


@login_required
@user_passes_test(lambda u: u.has_perm("appkfet.can_add_bucquage"))
def list_events_to_bucque(request):
    list_of_event_to_bucque = Event.objects.filter(ended=False)
    return render(
        request, "appevents/listeventstobucque.html", {"list": list_of_event_to_bucque}
    )


@login_required
@user_passes_test(lambda u: u.has_perm("appkfet.can_add_bucquage"))
def event_to_bucque(request, event):
    if request.method == "POST":
        form = BucqueEventForm(request.POST, request.FILES)
        if form.is_valid():
            error = manage_participation_file(request.FILES["file"], event)
            url = reverse("downloadreport", args=event)
            if error == 0:
                msg = """Le bucquage a été réalisé sans erreur, le rapport est disponible <a href='{url}'>ici</a>"""
                messages.success(request, mark_safe(msg.format(url=url)))
            else:
                msg = """Le bucquage a été réalisé avec des erreurs, le rapport est disponible <a href='{url}'>ici</a>"""
                messages.warning(request, mark_safe(msg.format(url=url)))
            return redirect(list_events_to_bucque)
    else:
        form = BucqueEventForm()
    return render(
        request, "appevents/eventtobucque.html", {"form": form, "event": event}
    )


def manage_participation_file(file, event):
    error = 0
    book = xlrd.open_workbook(
        file_contents=file.read(), encoding_override="utf-8"
    )  # lecture du fichier importé
    sheet = book.sheet_by_name("Event")
    row_count = sheet.nrows
    col_count = sheet.ncols
    # définition du fichier de sortie (rapport). On fait une copie du fichier importé et on rajoute une colonne commentaire
    outbook = copy(book)
    outsheet = outbook.get_sheet(0)
    comment_col = 9
    font_style = xlwt.XFStyle()
    outsheet.write(
        0, comment_col, "Commentaire", font_style
    )  # ajout du titre de la colonne commentaire
    # écriture des fichiers
    for cur_row in range(1, row_count):
        id_participation = sheet.cell(cur_row, 0).value
        username = sheet.cell(cur_row, 1).value
        id_produit = sheet.cell(cur_row, 4).value
        quantity = sheet.cell(cur_row, 6).value
        participation_ok = sheet.cell(cur_row, 7).value
        participation_bucquee = sheet.cell(cur_row, 8).value
        if id_participation != "":  # si l'ID participation n'est pas vide alors
            if (
                ParticipationEvent.objects.filter(pk=id_participation).count() == 1
            ):  # si l'ID participation correspond à une participation qui existe
                targetparticipation = ParticipationEvent.objects.get(
                    pk=id_participation
                )  # récupération de l'objet participation
                if (
                    str(targetparticipation.product_participation.parent_event.pk)
                    == event
                ):  # si la participation correspond à l'évènement en cours de bucquage
                    if (
                        targetparticipation.participation_bucquee is False
                    ):  # si la participation en base n'est pas déjà bucquée
                        if (
                            participation_ok == 1
                        ):  # si la participation est validée sur le fichier, vérification de la cohérence de la ligne par rapport aux informations en base
                            if (
                                id_produit
                                == targetparticipation.product_participation.pk
                            ):  # si le produit renseigné dans le fichier est le même que celui enregistré en base
                                if (
                                    username
                                    == targetparticipation.cible_participation.consommateur.username
                                ):  # si le consommateur renseigné dans le fichier est le même que celui enregistré en base
                                    targetparticipation.participation_ok = True  # passage à True dans l'objet participation en base
                                    targetparticipation.number = quantity  # application de la bonne quantité dans l'objet participation en base
                                    prixtotal = (
                                        Decimal(quantity)
                                        * targetparticipation.product_participation.prix
                                    )  # vérification que le consommateur a assez d'argent sur son compte pour cette participation
                                    if targetparticipation.cible_participation.testdebit(
                                        prixtotal
                                    ):
                                        outsheet.write(cur_row, 8, "TRUE", font_style)
                                        targetparticipation.save()  # sauvegarde et bucquage via la méthode du modèle
                                        outsheet.write(
                                            cur_row,
                                            comment_col,
                                            "La participation a été bucquée",
                                            font_style,
                                        )
                                    else:
                                        outsheet.write(
                                            cur_row,
                                            comment_col,
                                            "Le consommateur n'a pas assez d'argent sur son compte",
                                            font_style,
                                        )
                                        error = +1
                                else:
                                    outsheet.write(
                                        cur_row,
                                        comment_col,
                                        "Le consommateur renseigné dans le fichier n'est pas le même que celui enregistré en base",
                                        font_style,
                                    )
                                    error = +1
                            else:
                                outsheet.write(
                                    cur_row,
                                    comment_col,
                                    "Le produit renseigné dans le fichier n'est pas le même que celui enregistré en base",
                                    font_style,
                                )
                                error = +1
                        else:
                            outsheet.write(
                                cur_row,
                                comment_col,
                                "La participation n'est pas validée",
                                font_style,
                            )
                    else:
                        outsheet.write(cur_row, 8, "TRUE", font_style)
                        outsheet.write(
                            cur_row,
                            comment_col,
                            "La participation est déjà bucquée",
                            font_style,
                        )
                else:
                    outsheet.write(
                        cur_row,
                        comment_col,
                        "L'ID de cette participation ne correspond à l'évènement en cours de bucquage",
                        font_style,
                    )
                    error = +1
            else:
                outsheet.write(
                    cur_row,
                    comment_col,
                    "L'ID de cette participation n'existe pas",
                    font_style,
                )
                error = +1
        else:  # si la participation n'existe pas (la première case est vide)
            if (
                Consommateur.objects.filter(consommateur__username=username).count()
                == 1
            ):  # si le consommateur existe
                cible_participation = Consommateur.objects.get(
                    consommateur__username=username
                )
            else:
                error = +1
                outsheet.write(
                    cur_row,
                    comment_col,
                    "Le nom d'utilisateur n'existe pas",
                    font_style,
                )
            if (
                ProductEvent.objects.filter(pk=id_produit).count() == 1
            ):  # si le produit existe
                product_participation = ProductEvent.objects.get(pk=id_produit)
                if (
                    str(product_participation.parent_event.pk) == event
                ):  # si le produit appartient à l'event que je suis en train de bucquer
                    if participation_ok == 1:
                        participation_ok = True
                    else:
                        participation_ok = False
                    # création de la participation en base
                    ParticipationEvent.objects.get_or_create(
                        cible_participation=cible_participation,
                        product_participation=product_participation,
                        number=quantity,
                        participation_ok=participation_ok,
                    )
                    outsheet.write(cur_row, 8, "TRUE", font_style)
                    outsheet.write(
                        cur_row,
                        comment_col,
                        "La participation a été bucquée",
                        font_style,
                    )
                else:
                    error = +1
                    outsheet.write(
                        cur_row,
                        comment_col,
                        "Ce produit n'appartient pas à cet évènement",
                        font_style,
                    )
            else:
                outsheet.write(
                    cur_row, comment_col, "Le produit n'existe pas", font_style
                )
                error = +1
    # écriture du fichier de rapport dans un dossier du serveur
    filename = "report-event-" + str(event) + ".xls"
    filepath = os.path.join(
        MEDIA_ROOT, "report", filename
    )  # utilisation du dossier MEDIA_ROOT, sous dossier report
    outbook.save(filepath)
    # liaison du rapport avec l'évènement
    event = Event.objects.get(pk=event)
    event.report = filepath
    event.save()
    return error


# téléchargement du fichier de rapport pour un évènement donné
@login_required
@user_passes_test(lambda u: u.has_perm("appkfet.can_add_bucquage"))
def download_report(request, event):
    try:
        event = Event.objects.get(pk=event)
        response = HttpResponse(event.report, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="report.xls"'
        return response
    except Event.DoesNotExist:
        return redirect(list_events_to_bucque)
