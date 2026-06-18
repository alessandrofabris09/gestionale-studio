from django.urls import path

from . import views


urlpatterns = [
    path(
        'pratica/<int:pratica_id>/',
        views.lista_ore_pratica,
        name='lista_ore_pratica'
    ),
    path(
        'pratica/<int:pratica_id>/nuova/',
        views.nuova_voce_ora,
        name='nuova_voce_ora'
    ),
    path(
        'pratica/<int:pratica_id>/genera-parcella/',
        views.genera_parcella_da_ore,
        name='genera_parcella_da_ore'
    ),
    path(
        'voce/<int:voce_id>/modifica/',
        views.modifica_voce_ora,
        name='modifica_voce_ora'
    ),
    path(
        'voce/<int:voce_id>/elimina/',
        views.elimina_voce_ora,
        name='elimina_voce_ora'
    ),
]