from django.urls import path

from .views import (
    home,
    privacy_policy,
    termini_utilizzo,
    carica_workflow_base,
)


urlpatterns = [
    path('', home, name='home'),

    path('privacy/', privacy_policy, name='privacy_policy'),

    path('termini/', termini_utilizzo, name='termini_utilizzo'),

    path(
        'carica-workflow-base/<str:codice>/',
        carica_workflow_base,
        name='carica_workflow_base'
    ),
]