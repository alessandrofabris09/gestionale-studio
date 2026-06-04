import os
import resend

from datetime import date, datetime, time

from icalendar import Calendar, Event

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now

from studi.models import Studio
from studi.notifiche import get_email_notifiche_studio
from studi.email_templates import layout_email_base, tabella_email
from studi.utils import get_studio_utente
from studi.permessi import (
    puo_usare_agenda,
    puo_gestire_alert,
)

from attivita.models import Attivita

from .models import EventoAgenda
from .forms import EventoAgendaForm


CODICE_CRON_AGENDA = os.environ.get(
    'CODICE_CRON_AGENDA',
    'AGENDA1234'
)

CODICE_ICS_AGENDA = os.environ.get(
    'CODICE_ICS_AGENDA',
    'AGENDAICS1234'
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


def get_eventi_queryset(request):
    """
    Restituisce gli eventi agenda visibili dall'utente.

    Superuser:
    - vede tutti gli eventi

    Utente normale:
    - vede solo gli eventi dello studio collegato
    """

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        return EventoAgenda.objects.all()

    return EventoAgenda.objects.filter(
        studio=studio
    )


@login_required
def lista_agenda(request):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    eventi = get_eventi_queryset(request).filter(
        completato=False
    ).order_by(
        'data',
        'ora_inizio'
    )

    return render(
        request,
        'agenda/lista_agenda.html',
        {
            'eventi': eventi
        }
    )


@login_required
def agenda_oggi(request):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    oggi = date.today()

    eventi = get_eventi_queryset(request).filter(
        data=oggi,
        completato=False
    ).order_by(
        'ora_inizio'
    )

    return render(
        request,
        'agenda/agenda_oggi.html',
        {
            'eventi': eventi,
            'oggi': oggi,
        }
    )


@login_required
def nuovo_evento(request):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':

        form = EventoAgendaForm(
            request.POST,
            studio=studio
        )

        if form.is_valid():

            evento = form.save(commit=False)

            if not request.user.is_superuser:
                evento.studio = studio

            elif not evento.studio:
                evento.studio = studio

            evento.save()

            if evento.pratica:

                Attivita.objects.create(
                    pratica=evento.pratica,
                    utente=request.user,
                    tipo='ALTRO',
                    descrizione=(
                        f'Creato evento agenda: '
                        f'{evento.titolo}'
                    )
                )

            return redirect(
                'lista_agenda'
            )

    else:

        form = EventoAgendaForm(
            studio=studio
        )

    return render(
        request,
        'agenda/nuovo_evento.html',
        {
            'form': form
        }
    )


@login_required
def modifica_evento(request, evento_id):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    evento = get_object_or_404(
        get_eventi_queryset(request),
        id=evento_id
    )

    if request.method == 'POST':

        form = EventoAgendaForm(
            request.POST,
            instance=evento,
            studio=studio
        )

        if form.is_valid():

            evento = form.save(commit=False)

            if not request.user.is_superuser:
                evento.studio = studio

            evento.save()

            if evento.pratica:

                Attivita.objects.create(
                    pratica=evento.pratica,
                    utente=request.user,
                    tipo='MODIFICA',
                    descrizione=(
                        f'Modificato evento agenda: '
                        f'{evento.titolo}'
                    )
                )

            return redirect(
                'lista_agenda'
            )

    else:

        form = EventoAgendaForm(
            instance=evento,
            studio=studio
        )

    return render(
        request,
        'agenda/modifica_evento.html',
        {
            'form': form,
            'evento': evento,
        }
    )


@login_required
def elimina_evento(request, evento_id):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    evento = get_object_or_404(
        get_eventi_queryset(request),
        id=evento_id
    )

    pratica = evento.pratica
    titolo_evento = evento.titolo

    if request.method == 'POST':

        evento.delete()

        if pratica:

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='ELIMINAZIONE',
                descrizione=(
                    f'Eliminato evento agenda: '
                    f'{titolo_evento}'
                )
            )

        return redirect(
            'lista_agenda'
        )

    return render(
        request,
        'agenda/elimina_evento.html',
        {
            'evento': evento
        }
    )


@login_required
def completa_evento(request, evento_id):

    if not puo_usare_agenda(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    evento = get_object_or_404(
        get_eventi_queryset(request),
        id=evento_id
    )

    if evento.pratica:

        Attivita.objects.create(
            pratica=evento.pratica,
            utente=request.user,
            tipo='ALTRO',
            descrizione=(
                f'Completato evento agenda: '
                f'{evento.titolo}'
            )
        )

    evento.completato = True
    evento.save()

    return redirect(
        'lista_agenda'
    )


def invia_email_agenda_giornaliera(studio):
    """
    Invia allo studio una email riepilogativa degli eventi agenda di oggi.
    """

    oggi = now().date()

    eventi = EventoAgenda.objects.filter(
        studio=studio,
        data=oggi,
        completato=False
    ).order_by(
        'ora_inizio'
    )

    if not eventi.exists():

        return 'Nessun evento agenda per oggi.'

    email_destinatario = get_email_notifiche_studio(studio)

    if not email_destinatario:

        return 'Errore: nessuna email configurata per lo studio.'

    righe_tabella = []

    for evento in eventi:

        ora = (
            evento.ora_inizio.strftime('%H:%M')
            if evento.ora_inizio
            else '-'
        )

        cliente = (
            evento.cliente
            if evento.cliente
            else '-'
        )

        pratica = (
            evento.pratica
            if evento.pratica
            else '-'
        )

        descrizione = (
            evento.descrizione
            if evento.descrizione
            else '-'
        )

        righe_tabella.append([
            ora,
            evento.titolo,
            evento.get_tipo_display(),
            evento.get_priorita_display(),
            cliente,
            pratica,
            descrizione,
        ])

    tabella = tabella_email(
        headers=[
            'Ora',
            'Evento',
            'Tipo',
            'Priorità',
            'Cliente',
            'Pratica',
            'Note',
        ],
        rows=righe_tabella
    )

    contenuto_html = f"""
    <p style="font-size:16px;line-height:1.6;margin:0;color:#374151;">
        Gentile studio,
        <br>
        di seguito trovi il riepilogo degli eventi operativi previsti per oggi.
    </p>

    <div style="
        margin-top:24px;
        background:#f9fafb;
        border:1px solid #e5e7eb;
        border-radius:14px;
        padding:18px 20px;
    ">
        <div style="font-size:14px;color:#6b7280;font-weight:bold;text-transform:uppercase;letter-spacing:0.06em;">
            Agenda di oggi
        </div>

        <div style="font-size:34px;font-weight:bold;color:#111827;margin-top:6px;">
            {eventi.count()}
        </div>

        <div style="font-size:15px;color:#6b7280;margin-top:4px;">
            eventi programmati per il {oggi.strftime('%d/%m/%Y')}
        </div>
    </div>

    {tabella}
    """

    messaggio_html = layout_email_base(
        titolo='Agenda operativa di oggi',
        sottotitolo='Riepilogo automatico degli appuntamenti e delle attività dello studio.',
        contenuto_html=contenuto_html,
        testo_pulsante='Apri agenda',
        url_pulsante=settings.SITE_URL + '/agenda/'
    )

    resend.api_key = os.environ.get(
        'RESEND_API_KEY'
    )

    if not resend.api_key:

        return 'Errore: RESEND_API_KEY non configurata.'

    resend.Emails.send({
        "from": settings.EMAIL_FROM_NOTIFICHE,
        "to": [email_destinatario],
        "subject": "Agenda operativa di oggi - Studio Tecnico Cloud",
        "html": messaggio_html,
        "text": "Agenda operativa di oggi - Sono presenti eventi o attività da verificare nel gestionale Studio Tecnico Cloud.",
    })

    return 'Email agenda inviata correttamente.'


@login_required
def invia_agenda_email(request):

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

                messaggio = invia_email_agenda_giornaliera(
                    studio_item
                )

                messaggi.append(
                    f'{studio_item.nome}: {messaggio}'
                )

        else:

            messaggio = invia_email_agenda_giornaliera(
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
        'agenda/agenda_email_inviata.html',
        {
            'messaggio': '<br>'.join(messaggi)
        }
    )


def invia_agenda_email_cron(request, codice):

    if codice != CODICE_CRON_AGENDA:

        return redirect('/')

    messaggi = []

    try:

        studi = Studio.objects.filter(
            attivo=True
        ).order_by(
            'nome'
        )

        for studio in studi:

            messaggio = invia_email_agenda_giornaliera(
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
        'agenda/agenda_email_inviata.html',
        {
            'messaggio': '<br>'.join(messaggi)
        }
    )


def calendario_ics(request, codice):

    if codice != CODICE_ICS_AGENDA:

        return redirect('/')

    calendario = Calendar()

    calendario.add(
        'prodid',
        '-//Studio Tecnico Cloud//Agenda Operativa//IT'
    )

    calendario.add('version', '2.0')
    calendario.add('calscale', 'GREGORIAN')
    calendario.add('method', 'PUBLISH')

    eventi = EventoAgenda.objects.filter(
        completato=False
    ).order_by(
        'studio__nome',
        'data',
        'ora_inizio'
    )

    for evento_agenda in eventi:

        evento = Event()

        titolo = evento_agenda.titolo

        if evento_agenda.studio:
            titolo = f'{evento_agenda.studio.nome} - {titolo}'

        evento.add(
            'summary',
            titolo
        )

        descrizione = ''

        descrizione += (
            f'Tipo: '
            f'{evento_agenda.get_tipo_display()}\n'
        )

        descrizione += (
            f'Priorità: '
            f'{evento_agenda.get_priorita_display()}\n'
        )

        if evento_agenda.cliente:

            descrizione += (
                f'Cliente: '
                f'{evento_agenda.cliente}\n'
            )

        if evento_agenda.pratica:

            descrizione += (
                f'Pratica: '
                f'{evento_agenda.pratica}\n'
            )

        if evento_agenda.descrizione:

            descrizione += (
                f'Note: '
                f'{evento_agenda.descrizione}\n'
            )

        evento.add(
            'description',
            descrizione
        )

        ora_inizio = (
            evento_agenda.ora_inizio
            if evento_agenda.ora_inizio
            else time(9, 0)
        )

        ora_fine = (
            evento_agenda.ora_fine
            if evento_agenda.ora_fine
            else time(10, 0)
        )

        inizio = datetime.combine(
            evento_agenda.data,
            ora_inizio
        )

        fine = datetime.combine(
            evento_agenda.data,
            ora_fine
        )

        evento.add('dtstart', inizio)
        evento.add('dtend', fine)

        evento.add(
            'uid',
            f'evento-agenda-{evento_agenda.id}@studiotecnicocloud'
        )

        evento.add(
            'dtstamp',
            datetime.now()
        )

        calendario.add_component(evento)

    response = HttpResponse(
        calendario.to_ical(),
        content_type='text/calendar'
    )

    response[
        'Content-Disposition'
    ] = 'inline; filename="agenda_operativa.ics"'

    return response