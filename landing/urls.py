from django.urls import path

from .views import (
    home,
    privacy_policy,
    termini_utilizzo,
    ripristina_admin,
)


urlpatterns = [
    path('', home, name='home'),

    path('privacy/', privacy_policy, name='privacy_policy'),

    path('termini/', termini_utilizzo, name='termini_utilizzo'),

    path(
        'ripristina-admin/<str:codice>/',
        ripristina_admin,
        name='ripristina_admin'
    ),
]