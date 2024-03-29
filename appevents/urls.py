from django.urls import path

from . import views

urlpatterns = [
    path("listevents/", views.list_events, name="listevents"),
    path("subevent/<params>/<step>", views.sub_event, name="subevent"),
    path(
        "subproductevent/<finss>",
        views.sub_product_event,
        name="subproductevent",
    ),
    path("listeventstobucque", views.list_events_to_bucque, name="listeventstobucque"),
    path("eventtobucque/<event>", views.event_to_bucque, name="eventtobucque"),
]
