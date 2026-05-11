from django.core.management import call_command
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

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

    return render(request, 'scadenze/lista_scadenze.html', context)


@login_required
def nuova_scadenza(request):
    if request.method == 'POST':
        form = ScadenzaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_scadenze')
    else:
        form = ScadenzaForm()

    return render(request, 'scadenze/nuova_scadenza.html', {'form': form})


@login_required
def modifica_scadenza(request, scadenza_id):
    scadenza = get_object_or_404(Scadenza, id=scadenza_id)

    if request.method == 'POST':
        form = ScadenzaForm(request.POST, instance=scadenza)

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
    scadenza = get_object_or_404(Scadenza, id=scadenza_id)

    if request.method == 'POST':
        scadenza.delete()
        return redirect('lista_scadenze')

    return render(
        request,
        'scadenze/elimina_scadenza.html',
        {'scadenza': scadenza}
    )


    return render(request, 'scadenze/alert_scadenze.html', context)

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
def invia_alert_email_manuale(request):

    if not request.user.is_superuser:
        return redirect('/')

    try:
        call_command('invia_alert_scadenze')

        messaggio = 'Email alert scadenze inviata correttamente.'

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
        call_command('invia_alert_scadenze')
        messaggio = 'Alert email inviato correttamente.'
    except Exception as e:
        messaggio = f'Errore: {e}'

    return render(
        request,
        'scadenze/alert_email_inviato.html',
        {
            'messaggio': messaggio
        }
    )    