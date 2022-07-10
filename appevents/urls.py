from django.urls import path

from . import views

urlpatterns = [
    path("listevents/", views.list_events, name="listevents"),
    path("subevent/<params>/<step>", views.sub_event, name="subevent"),
    path(
        "subproductevent/<step>/<product_to_sub>",
        views.sub_product_event,
        name="subproductevent",
    ),
    path(
        "exportparticipationincsv/<event>",
        views.export_participation_in_csv,
        name="exportparticipationincsv",
    ),
    path(
        "exportparticipationinxls/<event>",
        views.export_participation_in_xls,
        name="exportparticipationinxls",
    ),
    path("listeventstobucque", views.list_events_to_bucque, name="listeventstobucque"),
    path("eventtobucque/<event>", views.event_to_bucque, name="eventtobucque"),
    path("downloadreport/<event>", views.download_report, name="downloadreport"),
]
