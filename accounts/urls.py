from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    CustomLoginView,
    CustomLogoutView,
    registrazione_studio,
)


urlpatterns = [
    path('recupero-password/', auth_views.PasswordResetView.as_view(
        template_name='registration/recupero_password.html',
        email_template_name='registration/recupero_password_email.txt',
    ), name='password_reset'),
    path('recupero-password/inviato/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/recupero_password.html',
        extra_context={'messaggio': 'Se esiste un account associato, riceverai un link per reimpostare la password.'},
    ), name='password_reset_done'),
    path('recupero-password/completato/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/recupero_password.html',
        extra_context={'messaggio': 'Password aggiornata. Puoi accedere con la nuova password.'},
    ), name='password_reset_complete'),
    path('recupero-password/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/recupero_password.html',
        extra_context={'conferma': True},
    ), name='password_reset_confirm'),
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
