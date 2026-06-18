from django.urls import path
from . import views

from .views import (
    home,
    ricerca_globale,
    backup_manuale,
)

urlpatterns = [
    path('', home, name='home'),
    path('ricerca/', ricerca_globale, name='ricerca_globale'),
    path('backup/', backup_manuale, name='backup_manuale'),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
]