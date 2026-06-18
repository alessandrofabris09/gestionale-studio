from django.urls import path
from . import views

from .views import (
    home,
    privacy_policy,
    termini,
    cookie_policy,
)


urlpatterns = [
    path('', home, name='home'),

    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),

    path("cookie-policy/", views.cookie_policy, name="cookie_policy"),

    path("termini/", views.termini, name="termini"),    
]