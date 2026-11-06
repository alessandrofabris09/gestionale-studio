from django.urls import path

from . import views


urlpatterns = [
    path(
        'checkout/pro/',
        views.checkout_pro,
        name='checkout_pro'
    ),

    path(
        'success/',
        views.checkout_success,
        name='checkout_success'
    ),

    path(
        'webhook/',
        views.stripe_webhook,
        name='stripe_webhook'
    ),
]