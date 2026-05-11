from django.urls import path

from .views import (
    lista_backup,
    crea_backup,
    scarica_backup,
)

urlpatterns = [
    path('', lista_backup, name='lista_backup'),
    path('crea/', crea_backup, name='crea_backup'),
    path('scarica/<str:filename>/', scarica_backup, name='scarica_backup'),
]