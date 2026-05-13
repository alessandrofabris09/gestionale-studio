from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now

import os
import resend
from datetime import date, timedelta

from .models import Scadenza
from .forms import ScadenzaForm
from agenda.models import EventoAgenda


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

            scadenza = form.save()

            if scadenza.pratica:

                EventoAgenda.objects.create(
                    titolo=f'Scadenza: {scadenza.titolo}',
                    tipo='SCADENZA',
                    priorita='MEDIA',
                    cliente=scadenza.pratica.cliente if scadenza.pratica.cliente else None,
                    pratica=scadenza.pratica,
                    data=scadenza.data_scadenza,
                    descrizione=f'Scadenza collegata alla pratica: {scadenza.pratica}'
                )

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

    righe_html = []

    for scadenza in scadenze:
        pratica = scadenza.pratica if scadenza.pratica else '-'

        righe_html.append(
            f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {scadenza.titolo}
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {scadenza.data_scadenza}
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {pratica}
                </td>
            </tr>
            """
        )

    messaggio_html = f"""
    <div style="font-family:Arial, sans-serif; color:#111827;">
        <h2>Alert scadenze - Gestionale Studio Tecnico</h2>

        <p>
            Di seguito le scadenze da verificare entro i prossimi 7 giorni.
        </p>

        <table style="border-collapse:collapse;width:100%;margin-top:20px;">
            <thead>
                <tr style="background:#111827;color:white;">
                    <th style="padding:10px;text-align:left;">Scadenza</th>
                    <th style="padding:10px;text-align:left;">Data</th>
                    <th style="padding:10px;text-align:left;">Pratica</th>
                </tr>
            </thead>
            <tbody>
                {''.join(righe_html)}
            </tbody>
        </table>

        <p style="margin-top:25px;color:#6b7280;font-size:13px;">
            Email generata automaticamente dal Gestionale Studio Tecnico.
        </p>
    </div>
    """

    resend.api_key = os.environ.get('RESEND_API_KEY')

    if not resend.api_key:
        return 'Errore: RESEND_API_KEY non configurata.'

    resend.Emails.send({
        "from": "Gestionale Studio <onboarding@resend.dev>",
        "to": [settings.ALERT_EMAIL],
        "subject": "Alert scadenze - Gestionale Studio Tecnico",
        "html": messaggio_html,
    })

    return 'Email alert scadenze inviata correttamente con Resend.'


@login_required
def invia_alert_email_manuale(request):

    if not request.user.is_superuser:
        return redirect('/')

    try:
        messaggio = invia_email_scadenze_leggera()

    except Exception as e:
        messaggio = f'Errore durante invio email: {e}'

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

    try:
        messaggio = invia_email_scadenze_leggera()

    except Exception as e:
        messaggio = f'Errore durante invio email: {e}'

    return render(
        request,
        'scadenze/alert_email_inviato.html',
        {
            'messaggio': messaggio
        }
    )