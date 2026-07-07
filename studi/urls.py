from django.urls import path

from .views import (
    abbonamento,
    profilo_studio,
    modifica_studio,
    utenti_studio,
    nuovo_utente_studio,
    modifica_ruolo_utente,
)

urlpatterns = [
    path(
        'abbonamento/',
        abbonamento,
        name='abbonamento'
    ),

    path(
        'profilo/',
        profilo_studio,
        name='profilo_studio'
    ),

    path(
        'profilo/modifica/',
        modifica_studio,
        name='modifica_studio'
    ),

    path(
        'utenti/',
        utenti_studio,
        name='utenti_studio'
    ),

    path(
        'utenti/nuovo/',
        nuovo_utente_studio,
        name='nuovo_utente_studio'
    ),

    path(
        'utenti/<int:profilo_id>/ruolo/',
        modifica_ruolo_utente,
        name='modifica_ruolo_utente'
    ),
]