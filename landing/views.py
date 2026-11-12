from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.http import require_safe

from .lancio import MESI_BETA_LANCIO, OBIETTIVO_ISCRIZIONI_FREE, POSTI_BETA_LANCIO
from .models import IscrizioneFreeLancio
from .seo import URL_CANONICO


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    return lancio(request)


@require_safe
def lancio(request):
    context = {'app_url': settings.SITE_URL.rstrip('/'), 'url_canonico': URL_CANONICO}
    if not settings.LANCIO_BETA_FREE:
        return render(request, 'landing/home.html', context)

    iscrizioni = IscrizioneFreeLancio.attive().count()
    context.update({
        'iscrizioni_free': iscrizioni,
        'obiettivo_iscrizioni_free': OBIETTIVO_ISCRIZIONI_FREE,
        'obiettivo_beta_raggiunto': iscrizioni >= OBIETTIVO_ISCRIZIONI_FREE,
        'posti_beta_lancio': POSTI_BETA_LANCIO,
        'mesi_beta_lancio': MESI_BETA_LANCIO,
    })
    return render(request, 'landing/campagna.html', context)


def privacy_policy(request):
    return render(request, "landing/privacy.html")


def cookie_policy(request):
    return render(request, "landing/cookie.html")


def termini(request):
    return render(request, "landing/termini.html")
