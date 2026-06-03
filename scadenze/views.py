from datetime import date, timedelta

import os
import resend

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now

from attivita.models import Attivita
from agenda.models import EventoAgenda

from studi.models import Studio
from studi.utils import get_studio_utente
from studi.notifiche import get_email_notifiche_studio
from studi.permessi import (
    puo_usare_agenda,
    puo_gestire_alert,
)

from .models import Scadenza
from .forms import ScadenzaForm


CODICE_CRON_ALERT = os.environ.get(
    'CODICE_CRON_ALERT',
    'ABCD1234'
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


def get_scadenze_queryset(request):
    """
    Restituisce le scadenze visibili dall'utente.

    Superuser:
    - vede tutte le scadenze

    Utente normale:
    - vede solo le scadenze dello studio collegato
    """

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        return Scadenza.objects.all()

    return Scadenza.objects.filter(
        pratica__studio=studio
    )


def get_eventi_agenda_queryset(request):
    """
    Restituisce gli eventi agenda visibili dall'utente.
    """

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        return EventoAgenda.objects.all()

    return EventoAgenda.objects.filter(
        studio=studio
    )


@login_required
def lista_scadenze(request):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    scadenze = get_scadenze_queryset(request).filter(
        completata=False
    ).order_by(
        'data_scadenza'
    )

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

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':

        form = ScadenzaForm(
            request.POST,
            studio=studio
        )

        if form.is_valid():

            scadenza = form.save()

            if scadenza.pratica:

                Attivita.objects.create(
                    pratica=scadenza.pratica,
                    utente=request.user,
                    tipo='SCADENZA',
                    descrizione=(
                        f'Creata scadenza: '
                        f'{scadenza.titolo}'
                    )
                )

                EventoAgenda.objects.create(
                    studio=studio,
                    titolo=f'Scadenza: {scadenza.titolo}',
                    tipo='SCADENZA',
                    priorita='MEDIA',
                    cliente=(
                        scadenza.pratica.cliente
                        if scadenza.pratica.cliente
                        else None
                    ),
                    pratica=scadenza.pratica,
                    data=scadenza.data_scadenza,
                    descrizione=(
                        f'Scadenza collegata alla pratica: '
                        f'{scadenza.pratica}'
                    )
                )

            return redirect(
                'lista_scadenze'
            )

    else:

        form = ScadenzaForm(
            studio=studio
        )

    return render(
        request,
        'scadenze/nuova_scadenza.html',
        {
            'form': form
        }
    )


@login_required
def modifica_scadenza(request, scadenza_id):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    scadenza = get_object_or_404(
        get_scadenze_queryset(request),
        id=scadenza_id
    )

    if request.method == 'POST':

        form = ScadenzaForm(
            request.POST,
            instance=scadenza,
            studio=studio
        )

        if form.is_valid():

            scadenza = form.save()

            if scadenza.pratica:

                Attivita.objects.create(
                    pratica=scadenza.pratica,
                    utente=request.user,
                    tipo='MODIFICA',
                    descrizione=(
                        f'Modificata scadenza: '
                        f'{scadenza.titolo}'
                    )
                )

            return redirect(
                'lista_scadenze'
            )

    else:

        form = ScadenzaForm(
            instance=scadenza,
            studio=studio
        )

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

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    scadenza = get_object_or_404(
        get_scadenze_queryset(request),
        id=scadenza_id
    )

    if request.method == 'POST':

        if scadenza.pratica:

            Attivita.objects.create(
                pratica=scadenza.pratica,
                utente=request.user,
                tipo='ELIMINAZIONE',
                descrizione=(
                    f'Eliminata scadenza: '
                    f'{scadenza.titolo}'
                )
            )

        scadenza.delete()

        return redirect(
            'lista_scadenze'
        )

    return render(
        request,
        'scadenze/elimina_scadenza.html',
        {
            'scadenza': scadenza
        }
    )


@login_required
def completa_scadenza(request, scadenza_id):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    scadenza = get_object_or_404(
        get_scadenze_queryset(request),
        id=scadenza_id
    )

    if scadenza.pratica:

        Attivita.objects.create(
            pratica=scadenza.pratica,
            utente=request.user,
            tipo='SCADENZA',
            descrizione=(
                f'Completata scadenza: '
                f'{scadenza.titolo}'
            )
        )

    scadenza.completata = True
    scadenza.save()

    return redirect(
        'lista_scadenze'
    )


@login_required
def calendario_scadenze(request):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    return render(
        request,
        'scadenze/calendario.html'
    )


@login_required
def alert_scadenze(request):

    if not puo_gestire_alert(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    oggi = date.today()

    limite = oggi + timedelta(days=7)

    scadenze = get_scadenze_queryset(request)

    scadute = scadenze.filter(
        completata=False,
        data_scadenza__lt=oggi
    ).order_by(
        'data_scadenza'
    )

    imminenti = scadenze.filter(
        completata=False,
        data_scadenza__gte=oggi,
        data_scadenza__lte=limite
    ).order_by(
        'data_scadenza'
    )

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

    if not puo_usare_agenda(request):
        return JsonResponse(
            [],
            safe=False
        )

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return JsonResponse(
            [],
            safe=False
        )

    eventi = []

    scadenze = get_scadenze_queryset(request)

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
            'title': f'📌 {scadenza.titolo}',
            'start': scadenza.data_scadenza.isoformat(),
            'color': colore,
            'url': url,
        })

    eventi_agenda = get_eventi_agenda_queryset(request)

    for evento in eventi_agenda:

        colore = '#2563eb'

        if evento.priorita == 'ALTA':
            colore = '#dc2626'

        elif evento.priorita == 'MEDIA':
            colore = '#ca8a04'

        elif evento.priorita == 'BASSA':
            colore = '#16a34a'

        eventi.append({
            'title': f'🗓️ {evento.titolo}',
            'start': evento.data.isoformat(),
            'color': colore,
        })

    return JsonResponse(
        eventi,
        safe=False
    )


def invia_email_scadenze_leggera(studio):

    oggi = now().date()

    limite = oggi + timedelta(days=7)

    scadenze = Scadenza.objects.filter(
        pratica__studio=studio,
        completata=False,
        data_scadenza__gte=oggi,
        data_scadenza__lte=limite
    ).order_by(
        'data_scadenza'
    )

    if not scadenze.exists():

        return 'Nessuna scadenza da notificare.'

    righe_html = []

    for scadenza in scadenze:

        pratica = (
            scadenza.pratica
            if scadenza.pratica
            else '-'
        )

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

        <h2>
            Alert scadenze - Gestionale Studio Tecnico
        </h2>

        <p>
            Di seguito le scadenze da verificare entro i prossimi 7 giorni.
        </p>

        <table style="border-collapse:collapse;width:100%;margin-top:20px;">

            <thead>

                <tr style="background:#111827;color:white;">

                    <th style="padding:10px;text-align:left;">
                        Scadenza
                    </th>

                    <th style="padding:10px;text-align:left;">
                        Data
                    </th>

                    <th style="padding:10px;text-align:left;">
                        Pratica
                    </th>

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

    resend.api_key = os.environ.get(
        'RESEND_API_KEY'
    )

    if not resend.api_key:

        return 'Errore: RESEND_API_KEY non configurata.'

    email_destinatario = get_email_notifiche_studio(studio)

    if not email_destinatario:
        return 'Errore: nessuna email configurata per lo studio.'

    resend.Emails.send({
        "from": "Gestionale Studio <onboarding@resend.dev>",
        "to": [email_destinatario],
        "subject": "Alert scadenze - Gestionale Studio Tecnico",
        "html": messaggio_html,
    })

    return 'Email alert scadenze inviata correttamente con Resend.'


@login_required
def invia_alert_email_manuale(request):

    if not puo_gestire_alert(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    messaggi = []

    try:

        if request.user.is_superuser and not studio:

            studi = Studio.objects.filter(
                attivo=True
            ).order_by(
                'nome'
            )

            for studio_item in studi:

                messaggio = invia_email_scadenze_leggera(
                    studio_item
                )

                messaggi.append(
                    f'{studio_item.nome}: {messaggio}'
                )

        else:

            messaggio = invia_email_scadenze_leggera(
                studio
            )

            messaggi.append(
                messaggio
            )

    except Exception as e:

        messaggi.append(
            f'Errore durante invio email: {e}'
        )

    return render(
        request,
        'scadenze/alert_email_inviato.html',
        {
            'messaggio': '<br>'.join(messaggi)
        }
    )


def invia_alert_email_cron(request, codice):

    if codice != CODICE_CRON_ALERT:

        return redirect('/')

    messaggi = []

    try:

        studi = Studio.objects.filter(
            attivo=True
        ).order_by(
            'nome'
        )

        for studio in studi:

            messaggio = invia_email_scadenze_leggera(
                studio
            )

            messaggi.append(
                f'{studio.nome}: {messaggio}'
            )

    except Exception as e:

        messaggi.append(
            f'Errore durante invio email: {e}'
        )

    return render(
        request,
        'scadenze/alert_email_inviato.html',
        {
            'messaggio': '<br>'.join(messaggi)
        }
    )