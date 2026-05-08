from django.urls import path

from .views import (
    lista_pratiche,
    nuova_pratica,
    dettaglio_pratica,
    modifica_pratica,
    elimina_pratica,
    pdf_pratica,
)

urlpatterns = [
    path('', lista_pratiche, name='lista_pratiche'),
    path('nuova/', nuova_pratica, name='nuova_pratica'),
    path('<int:pratica_id>/', dettaglio_pratica, name='dettaglio_pratica'),
    path('<int:pratica_id>/modifica/', modifica_pratica, name='modifica_pratica'),
    path('<int:pratica_id>/elimina/', elimina_pratica, name='elimina_pratica'),
    path('<int:pratica_id>/pdf/', pdf_pratica, name='pdf_pratica'),
]