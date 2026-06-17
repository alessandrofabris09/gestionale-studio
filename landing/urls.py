from django.urls import path

from .views import (
    home,
    privacy_policy,
    termini_utilizzo,
    carica_tipi_pratica,
)


urlpatterns = [
    path('', home, name='home'),

    path('privacy/', privacy_policy, name='privacy_policy'),

    path('termini/', termini_utilizzo, name='termini_utilizzo'),

    path(
        'carica-tipi-pratica/<str:codice>/',
        carica_tipi_pratica,
        name='carica_tipi_pratica'
    ),
]