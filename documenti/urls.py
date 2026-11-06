from django.urls import path

from .views import (
    lista_documenti,
    carica_documento,
    carica_documenti_multipli,
    elimina_documento,
    verifica_documenti_cloud,
)

urlpatterns = [

    path(
        '',
        lista_documenti,
        name='lista_documenti'
    ),

    path(
        'pratica/<int:pratica_id>/carica/',
        carica_documento,
        name='carica_documento'
    ),

    path(
        'pratica/<int:pratica_id>/carica-multipli/',
        carica_documenti_multipli,
        name='carica_documenti_multipli'
    ),

    path(
        '<int:documento_id>/elimina/',
        elimina_documento,
        name='elimina_documento'
    ),

    path(
        'verifica-cloud/',
        verifica_documenti_cloud,
        name='verifica_documenti_cloud'
    ),

]