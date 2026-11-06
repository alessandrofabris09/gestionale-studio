from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.lista_utenti,
        name='lista_utenti'
    ),

    path(
        'nuovo/',
        views.nuovo_utente,
        name='nuovo_utente'
    ),

    path(
        'registrazione/',
        views.registrazione_studio,
        name='registrazione_studio'
    ),

]