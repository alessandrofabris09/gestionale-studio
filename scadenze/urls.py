from django.urls import path

from .views import (
    invia_alert_email_cron,
    lista_scadenze,
    nuova_scadenza,
    modifica_scadenza,
    elimina_scadenza,
    calendario_scadenze,
    alert_scadenze,
    eventi_calendario,
    invia_alert_email_manuale,
)

urlpatterns = [
    path('', lista_scadenze, name='lista_scadenze'),
    path('nuova/', nuova_scadenza, name='nuova_scadenza'),
    path('<int:scadenza_id>/modifica/', modifica_scadenza, name='modifica_scadenza'),
    path('<int:scadenza_id>/elimina/', elimina_scadenza, name='elimina_scadenza'),
    path('calendario/', calendario_scadenze, name='calendario_scadenze'),
    path('alert/', alert_scadenze, name='alert_scadenze'),
    path('eventi/', eventi_calendario, name='eventi_calendario'),
    path('invia-alert-email/', invia_alert_email_manuale, name='invia_alert_email_manuale'),
    path(
    'invia-alert-email-cron/<str:codice>/',
    invia_alert_email_cron,
    name='invia_alert_email_cron'
),