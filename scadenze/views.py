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


@login_required
def calendario_scadenze(request):
    oggi = date.today()

    anno = int(request.GET.get('anno', oggi.year))
    mese = int(request.GET.get('mese', oggi.month))

    cal = calendar.Calendar(firstweekday=0)
    giorni_mese = cal.monthdatescalendar(anno, mese)

    scadenze = Scadenza.objects.filter(
        data_scadenza__year=anno,
        data_scadenza__month=mese
    )

    scadenze_per_giorno = {}

    for scadenza in scadenze:
        giorno = scadenza.data_scadenza

        if giorno not in scadenze_per_giorno:
            scadenze_per_giorno[giorno] = []

        scadenze_per_giorno[giorno].append(scadenza)

    if mese == 1:
        mese_precedente = 12
        anno_precedente = anno - 1
    else:
        mese_precedente = mese - 1
        anno_precedente = anno

    if mese == 12:
        mese_successivo = 1
        anno_successivo = anno + 1
    else:
        mese_successivo = mese + 1
        anno_successivo = anno

    context = {
        'anno': anno,
        'mese': mese,
        'nome_mese': calendar.month_name[mese],
        'giorni_mese': giorni_mese,
        'scadenze_per_giorno': scadenze_per_giorno,
        'mese_precedente': mese_precedente,
        'anno_precedente': anno_precedente,
        'mese_successivo': mese_successivo,
        'anno_successivo': anno_successivo,
        'oggi': oggi,
    }

    return render(request, 'scadenze/calendario_scadenze.html', context)


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

    return render(request, 'scadenze/alert_scadenze.html', context)