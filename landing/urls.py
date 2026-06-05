from django.urls import path

from .views import (
    home,
    privacy_policy,
    termini_utilizzo,
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
]