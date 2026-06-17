from django.urls import path

from .views import (
    home,
    privacy_policy,
    termini_utilizzo,
    carica_workflow_professionali,
)


urlpatterns = [
    path('', home, name='home'),

    path('privacy/', privacy_policy, name='privacy_policy'),

    path('termini/', termini_utilizzo, name='termini_utilizzo'),

    path(
        'carica-workflow-professionali/<str:codice>/',
        carica_workflow_professionali,
        name='carica_workflow_professionali'
    ),
]