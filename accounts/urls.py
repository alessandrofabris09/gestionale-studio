from django.urls import path

from .views import (
    CustomLoginView,
    CustomLogoutView,
    registrazione_studio,
)


urlpatterns = [
    path(
        'login/',
        CustomLoginView.as_view(),
        name='accounts_login'
    ),

    path(
        'logout/',
        CustomLogoutView.as_view(),
        name='accounts_logout'
    ),

    path(
        'registrazione/',
        registrazione_studio,
        name='registrazione_studio'
    ),
]