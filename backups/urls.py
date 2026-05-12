from django.urls import path

from .views import (
    lista_backup,
    crea_backup,
    scarica_backup,
    crea_backup_cron,
)

urlpatterns = [
    path('', lista_backup, name='lista_backup'),
    path('crea/', crea_backup, name='crea_backup'),
    path('scarica/<str:filename>/', scarica_backup, name='scarica_backup'),
    path(
    'cron/<str:codice>/',
    crea_backup_cron,
    name='crea_backup_cron'
),
]