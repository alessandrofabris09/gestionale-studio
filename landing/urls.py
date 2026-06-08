from django.urls import path

from .views import (
    home,
    privacy_policy,
    termini_utilizzo,
    crea_superuser_iniziale,
)


urlpatterns = [
    path(
        '',
        home,
        name='home'
    ),

    path(
        'privacy/',
        privacy_policy,
        name='privacy_policy'
    ),

    path(
        'termini/',
        termini_utilizzo,
        name='termini_utilizzo'
    ),

    path(
        'crea-superuser/<str:codice>/',
        crea_superuser_iniziale,
        name='crea_superuser_iniziale'
    ),
]