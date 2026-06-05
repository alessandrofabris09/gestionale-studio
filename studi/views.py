from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404

from django.utils import timezone

from .utils import get_studio_utente

from .models import ProfiloUtente
from .forms import StudioForm, ProfiloUtenteRuoloForm

from studi.permessi import (
    puo_gestire_abbonamento,
    puo_gestire_utenti,
)


def accesso_negato(request):
    """
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )


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


@login_required
def profilo_studio(request):
    """
    Pagina riepilogativa dei dati dello studio.

    Il titolare può accedere alla modifica.
    Gli altri utenti possono visualizzare i dati.
    """

    studio = get_studio_utente(request)

    if not studio:
        logout(request)
        return redirect('login')

    utenti_studio = ProfiloUtente.objects.filter(
        studio=studio
    ).select_related(
        'user'
    ).order_by(
        'ruolo',
        'user__username'
    )

    context = {
        'studio': studio,
        'utenti_studio': utenti_studio,
        'puo_modificare': puo_gestire_utenti(request),
    }

    return render(
        request,
        'studi/profilo_studio.html',
        context
    )


@login_required
def modifica_studio(request):
    """
    Modifica dati anagrafici dello studio.

    Consentita solo a:
    - superuser
    - TITOLARE
    """

    studio = get_studio_utente(request)

    if not studio:
        logout(request)
        return redirect('login')

    if not puo_gestire_utenti(request):
        return accesso_negato(request)

    if request.method == 'POST':

        form = StudioForm(
            request.POST,
            instance=studio
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Dati dello studio aggiornati correttamente.'
            )

            return redirect(
                'profilo_studio'
            )

    else:

        form = StudioForm(
            instance=studio
        )

    context = {
        'form': form,
        'studio': studio,
    }

    return render(
        request,
        'studi/modifica_studio.html',
        context
    )


@login_required
def utenti_studio(request):
    """
    Elenco utenti collegati allo studio.

    Consentito solo a:
    - superuser
    - TITOLARE
    """

    studio = get_studio_utente(request)

    if not studio:
        logout(request)
        return redirect('login')

    if not puo_gestire_utenti(request):
        return accesso_negato(request)

    profili = ProfiloUtente.objects.filter(
        studio=studio
    ).select_related(
        'user'
    ).order_by(
        'ruolo',
        'user__username'
    )

    context = {
        'studio': studio,
        'profili': profili,
    }

    return render(
        request,
        'studi/utenti_studio.html',
        context
    )


@login_required
def modifica_ruolo_utente(request, profilo_id):
    """
    Modifica i dati principali e il ruolo di un utente dello stesso studio.

    Regole:
    - solo titolare/superuser
    - solo utenti dello stesso studio
    - il titolare non può togliere a sé stesso il ruolo TITOLARE
    """

    studio = get_studio_utente(request)

    if not studio:
        logout(request)
        return redirect('login')

    if not puo_gestire_utenti(request):
        return accesso_negato(request)

    profilo = get_object_or_404(
        ProfiloUtente.objects.select_related(
            'user',
            'studio'
        ),
        id=profilo_id,
        studio=studio
    )

    if request.method == 'POST':

        form = ProfiloUtenteRuoloForm(
            request.POST,
            instance=profilo
        )

        if form.is_valid():

            nuovo_ruolo = form.cleaned_data.get(
                'ruolo'
            )

            if (
                profilo.user == request.user and
                profilo.ruolo == 'TITOLARE' and
                nuovo_ruolo != 'TITOLARE'
            ):

                messages.error(
                    request,
                    'Non puoi rimuovere il ruolo TITOLARE dal tuo stesso utente.'
                )

                return redirect(
                    'utenti_studio'
                )

            form.save()

            messages.success(
                request,
                'Dati utente aggiornati correttamente.'
            )

            return redirect(
                'utenti_studio'
            )

    else:

        form = ProfiloUtenteRuoloForm(
            instance=profilo
        )

    context = {
        'form': form,
        'profilo': profilo,
        'studio': studio,
    }

    return render(
        request,
        'studi/modifica_ruolo_utente.html',
        context
    )