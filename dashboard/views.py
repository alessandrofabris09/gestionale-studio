import shutil

from pathlib import Path
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect
from django.utils.timezone import now

from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from scadenze.models import Scadenza
from documenti.models import Documento
from parcelle.models import Parcella
from agenda.models import EventoAgenda


@login_required
def home(request):

    pratiche_aperte = Pratica.objects.exclude(
        stato='CONCLUSA'
    ).count()

    pratiche_chiuse = Pratica.objects.filter(
        stato='CONCLUSA'
    ).count()

    scadenze_imminenti = Scadenza.objects.filter(
        data_scadenza__lte=now().date() + timedelta(days=30),
        completata=False
    ).count()

    totale_parcelle = Parcella.objects.aggregate(
        totale=Sum('importo')
    )['totale'] or 0

    totale_incassato = Parcella.objects.aggregate(
        totale=Sum('importo_pagato')
    )['totale'] or 0

    totale_da_incassare = totale_parcelle - totale_incassato

    parcelle_scadute = Parcella.objects.filter(
    stato='DA_PAGARE',
    data_scadenza__lt=now().date()
    ).count()

    ultime_parcelle = Parcella.objects.all().order_by('-id')[:5]

    ultime_pratiche = Pratica.objects.all().order_by('-id')[:5]

    ultime_scadenze = Scadenza.objects.all().order_by(
        'data_scadenza'
    )[:5]

    eventi_oggi = EventoAgenda.objects.filter(
    data=now().date()
    ).order_by(
        'ora_inizio'
    )[:5]

    pratiche_per_stato = list(
        Pratica.objects.values('stato')
        .annotate(totale=Count('id'))
        .order_by('stato')
    )

    parcelle_per_stato = list(
        Parcella.objects.values('stato')
        .annotate(totale=Count('id'))
        .order_by('stato')
    )

    labels_pratiche = [
        item['stato'] for item in pratiche_per_stato
    ]

    dati_pratiche = [
        item['totale'] for item in pratiche_per_stato
    ]

    labels_parcelle = [
        item['stato'] for item in parcelle_per_stato
    ]

    dati_parcelle = [
        item['totale'] for item in parcelle_per_stato
    ]

    context = {
        'tot_clienti': Cliente.objects.count(),
        'tot_immobili': Immobile.objects.count(),
        'tot_pratiche': Pratica.objects.count(),
        'tot_scadenze': Scadenza.objects.count(),

        'pratiche_aperte': pratiche_aperte,
        'pratiche_chiuse': pratiche_chiuse,
        'scadenze_imminenti': scadenze_imminenti,

        'totale_parcelle': totale_parcelle,
        'totale_incassato': totale_incassato,
        'totale_da_incassare': totale_da_incassare,
        'parcelle_scadute': parcelle_scadute,
        'ultime_parcelle': ultime_parcelle,

        'ultime_pratiche': ultime_pratiche,
        'ultime_scadenze': ultime_scadenze,

        'labels_pratiche': labels_pratiche,
        'dati_pratiche': dati_pratiche,

        'labels_parcelle': labels_parcelle,
        'dati_parcelle': dati_parcelle,

        'eventi_oggi': eventi_oggi,
    }

    return render(
        request,
        'dashboard/home.html',
        context
    )


@login_required
def ricerca_globale(request):

    query = request.GET.get('q', '')

    clienti = []
    immobili = []
    pratiche = []
    scadenze = []
    documenti = []

    if query:

        clienti = Cliente.objects.filter(
            Q(nome__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query) |
            Q(codice_fiscale__icontains=query) |
            Q(partita_iva__icontains=query)
        )

        immobili = Immobile.objects.filter(
            Q(comune__icontains=query) |
            Q(indirizzo__icontains=query) |
            Q(foglio__icontains=query) |
            Q(mappale__icontains=query) |
            Q(subalterno__icontains=query) |
            Q(cliente__nome__icontains=query)
        )

        pratiche = Pratica.objects.filter(
            Q(oggetto__icontains=query) |
            Q(comune__icontains=query) |
            Q(protocollo__icontains=query) |
            Q(cliente__nome__icontains=query)
        )

        scadenze = Scadenza.objects.filter(
            Q(titolo__icontains=query) |
            Q(descrizione__icontains=query)
        )

        documenti = Documento.objects.filter(
            Q(titolo__icontains=query) |
            Q(note__icontains=query)
        )

    context = {
        'query': query,
        'clienti': clienti,
        'immobili': immobili,
        'pratiche': pratiche,
        'scadenze': scadenze,
        'documenti': documenti,
    }

    return render(
        request,
        'dashboard/ricerca.html',
        context
    )


@login_required
def backup_manuale(request):

    if not request.user.is_superuser:
        return redirect('/')

    base_dir = Path(settings.BASE_DIR)

    db_file = base_dir / 'db.sqlite3'
    backup_dir = base_dir / 'backup'

    timestamp = datetime.now().strftime(
        '%Y-%m-%d_%H-%M-%S'
    )

    backup_folder = (
        backup_dir /
        f'backup_manuale_{timestamp}'
    )

    backup_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    if db_file.exists():

        shutil.copy2(
            db_file,
            backup_folder / 'db.sqlite3'
        )

    return render(
        request,
        'dashboard/backup_ok.html',
        {
            'backup_folder': backup_folder
        }
    )