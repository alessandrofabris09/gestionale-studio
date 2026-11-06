from django.urls import path

from .views import (
    lista_agenda,
    agenda_oggi,
    nuovo_evento,
    completa_evento,
    modifica_evento,
    elimina_evento,
    invia_agenda_email,
    invia_agenda_email_cron,
    calendario_ics,
    sincronizza_calendario,
    rigenera_token_calendario,
)

urlpatterns = [

    path(
        '',
        lista_agenda,
        name='lista_agenda'
    ),

    path(
        'oggi/',
        agenda_oggi,
        name='agenda_oggi'
    ),

    path(
        'nuovo/',
        nuovo_evento,
        name='nuovo_evento'
    ),

    path('<int:evento_id>/completa/', completa_evento, name='completa_evento'),

    path(
        '<int:evento_id>/modifica/',
        modifica_evento,
        name='modifica_evento'
    ),

    path(
        '<int:evento_id>/elimina/',
        elimina_evento,
        name='elimina_evento'
    ),
    
    path(
        'sincronizza/',
        sincronizza_calendario,
        name='sincronizza_calendario'
    ),

    path(
        'sincronizza/rigenera-token/',
        rigenera_token_calendario,
        name='rigenera_token_calendario'
    ),

    path(
        'calendario/<str:codice>/.ics',
        calendario_ics,
        name='calendario_ics'
    ),

    path('invia-email/', invia_agenda_email, name='invia_agenda_email'),

    path('invia-email-cron/<str:codice>/', invia_agenda_email_cron, name='invia_agenda_email_cron'),

]