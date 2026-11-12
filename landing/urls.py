from django.urls import path
from . import seo, views

from .views import (
    home,
    privacy_policy,
    termini,
    cookie_policy,
)


urlpatterns = [
    path('robots.txt', seo.robots, name='landing_robots'),
    path('sitemap.xml', seo.sitemap, name='landing_sitemap'),
    path('', home, name='home'),
    path('lancio/', views.lancio, name='lancio_beta'),

    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),

    path("cookie-policy/", views.cookie_policy, name="cookie_policy"),

    path("termini/", views.termini, name="termini"),    
]
