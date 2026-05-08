import shutil

from pathlib import Path

from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from django.db.models import Q
from django.db.models import Sum
from django.db.models import Count

from django.contrib.auth.decorators import login_required
from django.utils.timezone import now

from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from scadenze.models import Scadenza
from documenti.models import Documento
from parcelle.models import Parcella

from accounts.decorators import group_required


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

    ultime_pratiche = Pratica.objects.all().order_by('-id')[:5]

    ultime_scadenze = Scadenza.objects.all().order_by(
        'data_scadenza'
    )[:5]

    pratiche_per_stato = Pratica.objects.values(
        'stato'
    ).annotate(
        totale=Count('id')
    ).order_by('stato')

    parcelle_per_stato = Parcella.objects.values(
        'stato'
    ).annotate(
        totale=Count('id')
    ).order_by('stato')

    max_pratiche_stato = 1

    for item in pratiche_per_stato:

        if item['totale'] > max_pratiche_stato:
            max_pratiche_stato = item['totale']

    max_parcelle_stato = 1

    for item in parcelle_per_stato:

        if item['totale'] > max_parcelle_stato:
            max_parcelle_stato = item['totale']

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

        'ultime_pratiche': ultime_pratiche,
        'ultime_scadenze': ultime_scadenze,

        'pratiche_per_stato': pratiche_per_stato,
        'parcelle_per_stato': parcelle_per_stato,

        'max_pratiche_stato': max_pratiche_stato,
        'max_parcelle_stato': max_parcelle_stato,
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

    backup_folder = backup_dir / f'backup_manuale_{timestamp}'

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