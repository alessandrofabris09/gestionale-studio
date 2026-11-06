from django.urls import path
from . import views

from .views import (
    home,
    ricerca_globale,
    backup_manuale,
    privacy_policy,
    termini,
    cookie_policy,
)

urlpatterns = [
    path('', home, name='home'),
    path('ricerca/', ricerca_globale, name='ricerca_globale'),
    path('backup/', backup_manuale, name='backup_manuale'),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("cookie-policy/", views.cookie_policy, name="cookie_policy"),
    path("termini/", views.termini, name="termini"),
]