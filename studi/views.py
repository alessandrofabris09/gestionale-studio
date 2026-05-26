from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.utils import timezone

from .utils import get_studio_utente


@login_required
def abbonamento(request):

    studio = get_studio_utente(request)

    giorni_trial = None

    if studio and studio.trial_fino_al:

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