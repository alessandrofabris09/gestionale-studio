from django.urls import path

from .views import (
    lista_immobili,
    nuovo_immobile,
    dettaglio_immobile,
    modifica_immobile,
    elimina_immobile,
)

urlpatterns = [

    path(
        '',
        lista_immobili,
        name='lista_immobili'
    ),

    path(
        'nuovo/',
        nuovo_immobile,
        name='nuovo_immobile'
    ),

    path(
        '<int:immobile_id>/',
        dettaglio_immobile,
        name='dettaglio_immobile'
    ),

    path(
        '<int:immobile_id>/modifica/',
        modifica_immobile,
        name='modifica_immobile'
    ),

    path(
        '<int:immobile_id>/elimina/',
        elimina_immobile,
        name='elimina_immobile'
    ),

]