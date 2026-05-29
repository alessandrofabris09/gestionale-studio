from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect

from django.utils import timezone

from .utils import get_studio_utente

from studi.permessi import puo_gestire_abbonamento


@login_required
def abbonamento(request):

    studio = get_studio_utente(request)

    if not studio:
        logout(request)
        return redirect('login')

    if not puo_gestire_abbonamento(request):
        return redirect('home')

    giorni_trial = None

    if studio.trial_fino_al:

        giorni_trial = (
            studio.trial_fino_al - timezone.now().date()
        ).days

        if giorni_trial < 0:
            giorni_trial = 0

    context = {
        'studio': studio,
        'giorni_trial': giorni_trial,
    }

    return render(
        request,
        'studi/abbonamento.html',
        context
    )