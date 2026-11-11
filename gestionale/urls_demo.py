from django.urls import path

from demo import views
from gestionale.cron import esegui_cron

urlpatterns = [
    path(
        'cron/pulisci-candidature/', esegui_cron,
        {'comando': 'pulisci_lista_pro', 'configurazione_token': 'DEMO_CLEANUP_CRON_TOKEN'},
        name='cron_pulisci_candidature',
    ),
    path('', views.home, name='demo_home'),
    path('prova/', views.prova, name='demo_prova'),
    path('pro/', views.lista, name='demo_lista'),
    path('pro/conferma/<uuid:token>/', views.conferma, name='demo_conferma'),
    path('pro/ritira/<uuid:token>/', views.ritira, name='demo_ritira'),
    path('privacy-policy/', views.privacy, name='demo_privacy'),
    path('cookie-policy/', views.cookie, name='demo_cookie'),
    path('termini/', views.termini, name='demo_termini'),
]
