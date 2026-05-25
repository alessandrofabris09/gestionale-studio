from django.urls import path

from . import views


urlpatterns = [

    path(
        'registrazione/',
        views.registrazione_studio,
        name='registrazione_studio'
    ),

]