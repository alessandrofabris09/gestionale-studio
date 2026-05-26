from django.urls import path

from . import views


urlpatterns = [
    path(
        'abbonamento/',
        views.abbonamento,
        name='abbonamento'
    ),
]