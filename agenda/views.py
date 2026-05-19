import os
import resend

from datetime import date, datetime, time
from icalendar import Calendar, Event

from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now

from .models import EventoAgenda
from .forms import EventoAgendaForm


@login_required
def lista_agenda(request):

    eventi = EventoAgenda.objects.filter(
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

    oggi = date.today()

    eventi = EventoAgenda.objects.filter(
        data=oggi
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

    if request.method == 'POST':

        form = EventoAgendaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_agenda')

    else:

        form = EventoAgendaForm()

    return render(
        request,
        'agenda/nuovo_evento.html',
        {
            'form': form
        }
    )


@login_required
def modifica_evento(request, evento_id):

    evento = get_object_or_404(
        EventoAgenda,
        id=evento_id
    )

    if request.method == 'POST':

        form = EventoAgendaForm(
            request.POST,
            instance=evento
        )

        if form.is_valid():
            form.save()
            return redirect('lista_agenda')

    else:

        form = EventoAgendaForm(instance=evento)

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

    evento = get_object_or_404(
        EventoAgenda,
        id=evento_id
    )

    if request.method == 'POST':

        evento.delete()

        return redirect('lista_agenda')

    return render(
        request,
        'agenda/elimina_evento.html',
        {
            'evento': evento
        }
    )


def invia_email_agenda_giornaliera():

    oggi = now().date()

    eventi = EventoAgenda.objects.filter(
        data=oggi
    ).order_by(
        'ora_inizio'
    )

    if not eventi.exists():
        return 'Nessun evento agenda per oggi.'

    righe = []

    for evento in eventi:

        ora = evento.ora_inizio if evento.ora_inizio else '-'
        cliente = evento.cliente if evento.cliente else '-'
        pratica = evento.pratica if evento.pratica else '-'
        descrizione = evento.descrizione if evento.descrizione else '-'

        righe.append(
            f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {ora}
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    <strong>{evento.titolo}</strong><br>
                    <span style="color:#6b7280;">{descrizione}</span>
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {evento.get_tipo_display()}
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {evento.get_priorita_display()}
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {cliente}
                </td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">
                    {pratica}
                </td>
            </tr>
            """
        )

    messaggio_html = f"""
    <div style="font-family:Arial, sans-serif; color:#111827;">

        <h2>Agenda operativa di oggi</h2>

        <p>
            Di seguito gli eventi programmati per oggi.
        </p>

        <table style="border-collapse:collapse;width:100%;margin-top:20px;">
            <thead>
                <tr style="background:#111827;color:white;">
                    <th style="padding:10px;text-align:left;">Ora</th>
                    <th style="padding:10px;text-align:left;">Evento</th>
                    <th style="padding:10px;text-align:left;">Tipo</th>
                    <th style="padding:10px;text-align:left;">Priorità</th>
                    <th style="padding:10px;text-align:left;">Cliente</th>
                    <th style="padding:10px;text-align:left;">Pratica</th>
                </tr>
            </thead>

            <tbody>
                {''.join(righe)}
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
        "subject": "Agenda operativa di oggi",
        "html": messaggio_html,
    })

    return 'Email agenda inviata correttamente.'


@login_required
def invia_agenda_email(request):

    if not request.user.is_superuser:
        return redirect('/')

    try:
        messaggio = invia_email_agenda_giornaliera()

    except Exception as e:
        messaggio = f'Errore durante invio email: {e}'

    return render(
        request,
        'agenda/agenda_email_inviata.html',
        {
            'messaggio': messaggio
        }
    )

@login_required
def completa_evento(request, evento_id):

    evento = get_object_or_404(
        EventoAgenda,
        id=evento_id
    )

    evento.completato = True
    evento.save()

    return redirect('lista_agenda')

def invia_agenda_email_cron(request, codice):

    if codice != 'AGENDA1234':
        return redirect('/')

    try:
        messaggio = invia_email_agenda_giornaliera()

    except Exception as e:
        messaggio = f'Errore durante invio email: {e}'

    return render(
        request,
        'agenda/agenda_email_inviata.html',
        {
            'messaggio': messaggio
        }
    )


def calendario_ics(request, codice):

    if codice != 'AGENDAICS1234':
        return redirect('/')
        
    calendario = Calendar()

    calendario.add('prodid', '-//Gestionale Studio Tecnico//Agenda Operativa//IT')
    calendario.add('version', '2.0')
    calendario.add('calscale', 'GREGORIAN')
    calendario.add('method', 'PUBLISH')

    eventi = EventoAgenda.objects.filter(
    completato=False
    ).order_by('data', 'ora_inizio')

    for evento_agenda in eventi:

        evento = Event()

        evento.add('summary', evento_agenda.titolo)

        descrizione = ''

        descrizione += f'Tipo: {evento_agenda.get_tipo_display()}\\n'
        descrizione += f'Priorità: {evento_agenda.get_priorita_display()}\\n'

        if evento_agenda.cliente:
            descrizione += f'Cliente: {evento_agenda.cliente}\\n'

        if evento_agenda.pratica:
            descrizione += f'Pratica: {evento_agenda.pratica}\\n'

        if evento_agenda.descrizione:
            descrizione += f'Note: {evento_agenda.descrizione}\\n'

        evento.add('description', descrizione)

        ora_inizio = evento_agenda.ora_inizio if evento_agenda.ora_inizio else time(9, 0)
        ora_fine = evento_agenda.ora_fine if evento_agenda.ora_fine else time(10, 0)

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
            f'evento-agenda-{evento_agenda.id}@gestionale-studio'
        )

        evento.add('dtstamp', datetime.now())

        calendario.add_component(evento)

    response = HttpResponse(
        calendario.to_ical(),
        content_type='text/calendar'
    )

    response['Content-Disposition'] = 'inline; filename="agenda_operativa.ics"'

    return response