from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now

import calendar
from datetime import date, timedelta

from .models import Scadenza
from .forms import ScadenzaForm


@login_required
def lista_scadenze(request):
    scadenze = Scadenza.objects.all().order_by('data_scadenza')

    context = {
        'scadenze': scadenze,
        'oggi': date.today(),
    }

    return render(
        request,
        'scadenze/lista_scadenze.html',
        context
    )


@login_required
def nuova_scadenza(request):
    if request.method == 'POST':
        form = ScadenzaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_scadenze')
    else:
        form = ScadenzaForm()

    return render(
        request,
        'scadenze/nuova_scadenza.html',
        {'form': form}
    )


@login_required
def modifica_scadenza(request, scadenza_id):
    scadenza = get_object_or_404(
        Scadenza,
        id=scadenza_id
    )

    if request.method == 'POST':
        form = ScadenzaForm(
            request.POST,
            instance=scadenza
        )

        if form.is_valid():
            form.save()
            return redirect('lista_scadenze')
    else:
        form = ScadenzaForm(instance=scadenza)

    return render(
        request,
        'scadenze/modifica_scadenza.html',
        {
            'form': form,
            'scadenza': scadenza,
        }
    )


@login_required
def elimina_scadenza(request, scadenza_id):
    scadenza = get_object_or_404(
        Scadenza,
        id=scadenza_id
    )

    if request.method == 'POST':
        scadenza.delete()
        return redirect('lista_scadenze')

    return render(
        request,
        'scadenze/elimina_scadenza.html',
        {'scadenza': scadenza}
    )


@login_required
def calendario_scadenze(request):
    return render(
        request,
        'scadenze/calendario.html'
    )


@login_required
def alert_scadenze(request):
    oggi = date.today()
    limite = oggi + timedelta(days=7)

    scadute = Scadenza.objects.filter(
        completata=False,
        data_scadenza__lt=oggi
    ).order_by('data_scadenza')

    imminenti = Scadenza.objects.filter(
        completata=False,
        data_scadenza__gte=oggi,
        data_scadenza__lte=limite
    ).order_by('data_scadenza')

    context = {
        'oggi': oggi,
        'scadute': scadute,
        'imminenti': imminenti,
    }

    return render(
        request,
        'scadenze/alert_scadenze.html',
        context
    )


@login_required
def eventi_calendario(request):
    scadenze = Scadenza.objects.all()

    eventi = []

    for scadenza in scadenze:

        colore = '#2563eb'

        if not scadenza.completata:
            if scadenza.data_scadenza < date.today():
                colore = '#dc2626'
            else:
                colore = '#ca8a04'
        else:
            colore = '#16a34a'

        url = ''

        if scadenza.pratica:
            url = reverse(
                'dettaglio_pratica',
                args=[scadenza.pratica.id]
            )

        eventi.append({
            'title': scadenza.titolo,
            'start': scadenza.data_scadenza.isoformat(),
            'color': colore,
            'url': url,
        })

    return JsonResponse(eventi, safe=False)


def invia_email_scadenze_leggera():
    oggi = now().date()
    limite = oggi + timedelta(days=7)

    scadenze = Scadenza.objects.filter(
        completata=False,
        data_scadenza__gte=oggi,
        data_scadenza__lte=limite
    ).order_by('data_scadenza')

    if not scadenze.exists():
        return 'Nessuna scadenza da notificare.'

    righe = []

    for scadenza in scadenze:
        pratica = scadenza.pratica if scadenza.pratica else '-'

        righe.append(
            f"- {scadenza.titolo}\n"
            f"  Data: {scadenza.data_scadenza}\n"
            f"  Pratica: {pratica}\n"
        )

    messaggio = (
        "Alert scadenze gestionale studio tecnico\n\n"
        "Scadenze da verificare entro i prossimi 7 giorni:\n\n"
        + "\n".join(righe)
    )

    send_mail(
        'Alert scadenze - Gestionale Studio Tecnico',
        messaggio,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ALERT_EMAIL],
        fail_silently=False,
    )

    return 'Email alert scadenze inviata correttamente.'


@login_required
def invia_alert_email_manuale(request):

    if not request.user.is_superuser:
        return redirect('/')

    messaggio = (
        'Invio SMTP disattivato sul sito Render per evitare blocchi del server. '
        'Usare il comando locale python manage.py invia_alert_scadenze oppure passare a Resend API.'
    )

    return render(
        request,
        'scadenze/alert_email_inviato.html',
        {
            'messaggio': messaggio
        }
    )

def invia_alert_email_cron(request, codice):

    if codice != 'ABCD1234':
        return redirect('/')

    return render(
        request,
        'scadenze/alert_email_inviato.html',
        {
            'messaggio': 'Cron ricevuto correttamente. Invio SMTP disattivato su Render per evitare blocchi del server.'
        }
    )