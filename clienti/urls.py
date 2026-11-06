from django.urls import path

from .views import (
    lista_clienti,
    nuovo_cliente,
    dettaglio_cliente,
    modifica_cliente,
    elimina_cliente,
)

urlpatterns = [
    path('', lista_clienti, name='lista_clienti'),

    path(
        'nuovo/',
        nuovo_cliente,
        name='nuovo_cliente'
    ),

    path(
        '<int:cliente_id>/',
        dettaglio_cliente,
        name='dettaglio_cliente'
    ),

    path(
        '<int:cliente_id>/modifica/',
        modifica_cliente,
        name='modifica_cliente'
    ),

    path(
        '<int:cliente_id>/elimina/',
        elimina_cliente,
        name='elimina_cliente'
    ),
]