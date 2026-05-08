from django.urls import path

from .views import (
    home,
    ricerca_globale,
    backup_manuale,
)

urlpatterns = [
    path('', home, name='home'),
    path('ricerca/', ricerca_globale, name='ricerca_globale'),
    path('backup/', backup_manuale, name='backup_manuale'),
]