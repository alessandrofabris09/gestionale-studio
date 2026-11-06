from django.urls import path

from .views import (
    lista_parcelle,
    nuova_parcella,
    modifica_parcella,
    elimina_parcella,
    pdf_parcella,
)

urlpatterns = [
    path('', lista_parcelle, name='lista_parcelle'),
    path('nuova/', nuova_parcella, name='nuova_parcella'),
    path('<int:parcella_id>/modifica/', modifica_parcella, name='modifica_parcella'),
    path('<int:parcella_id>/elimina/', elimina_parcella, name='elimina_parcella'),
    path('<int:parcella_id>/pdf/', pdf_parcella, name='pdf_parcella'),
]