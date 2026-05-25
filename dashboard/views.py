import shutil

from pathlib import Path
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.shortcuts import render, redirect
from django.utils.timezone import now

from studi.utils import get_studio_utente
from studi.models import Studio

from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from scadenze.models import Scadenza
from documenti.models import Documento
from parcelle.models import Parcella
from agenda.models import EventoAgenda


def get_studio_sicuro(request):
    studio = get_studio_utente(request)

    if studio:
        return studio

    return Studio.objects.first()


@login_required
def home(request):

    studio = get_studio_sicuro(request)

    pratiche = Pratica.objects.filter(
        studio=studio
    )

    pratiche_aperte = pratiche.exclude(
        stato='CONCLUSA'
    ).count()

    pratiche_chiuse = pratiche.filter(
        stato='CONCLUSA'
    ).count()

    scadenze = Scadenza.objects.filter(
        pratica__studio=studio
    )

    parcelle = Parcella.objects.filter(
        pratica__studio=studio
    )

    eventi = EventoAgenda.objects.filter(
        studio=studio
    )

    scadenze_imminenti = scadenze.filter(
        data_scadenza__lte=now().date() + timedelta(days=30),
        completata=False
    ).count()

    totale_parcelle = parcelle.aggregate(
        totale=Sum('importo')
    )['totale'] or 0

    totale_incassato = parcelle.aggregate(
        totale=Sum('importo_pagato')
    )['totale'] or 0

    totale_da_incassare = totale_parcelle - totale_incassato

    parcelle_scadute = parcelle.filter(
        stato='DA_PAGARE',
        data_scadenza__lt=now().date()
    ).count()

    ultime_parcelle = parcelle.order_by('-id')[:5]

    ultime_pratiche = pratiche.order_by('-id')[:5]

    ultime_scadenze = scadenze.order_by(
        'data_scadenza'
    )[:5]

    eventi_oggi = eventi.filter(
        data=now().date(),
        completato=False
    ).order_by(
        'ora_inizio'
    )[:5]

    pratiche_per_stato = list(
        pratiche.values(
            'stato'
        ).annotate(
            totale=Count('id')
        ).order_by(
            'stato'
        )
    )

    labels_pratiche = []

    dati_pratiche = []

    campo_stato_pratica = Pratica._meta.get_field('stato')

    for stato, label in campo_stato_pratica.choices:

        totale = pratiche.filter(
            stato=stato
        ).count()

        labels_pratiche.append(label)
        dati_pratiche.append(totale)

    labels_parcelle = []

    dati_parcelle = []

    campo_stato_parcella = Parcella._meta.get_field('stato')

    for stato, label in campo_stato_parcella.choices:

        totale = parcelle.filter(
            stato=stato
        ).count()

        labels_parcelle.append(label)
        dati_parcelle.append(totale)

    context = {
        'studio_corrente': studio,

        'tot_clienti': Cliente.objects.filter(
            studio=studio
        ).count(),

        'tot_immobili': Immobile.objects.filter(
            studio=studio
        ).count(),

        'tot_pratiche': pratiche.count(),

        'tot_scadenze': scadenze.count(),

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
        'eventi_oggi': eventi_oggi,

        'labels_pratiche': labels_pratiche,
        'dati_pratiche': dati_pratiche,

        'labels_parcelle': labels_parcelle,
        'dati_parcelle': dati_parcelle,
    }

    return render(
        request,
        'dashboard/home.html',
        context
    )


@login_required
def ricerca_globale(request):

    studio = get_studio_sicuro(request)

    query = request.GET.get('q', '')

    clienti = []
    immobili = []
    pratiche = []
    scadenze = []
    documenti = []

    if query:

        clienti = Cliente.objects.filter(
            studio=studio
        ).filter(
            Q(nome__icontains=query) |
            Q(email__icontains=query) |
            Q(telefono__icontains=query) |
            Q(codice_fiscale__icontains=query) |
            Q(partita_iva__icontains=query)
        )

        immobili = Immobile.objects.filter(
            studio=studio
        ).filter(
            Q(comune__icontains=query) |
            Q(indirizzo__icontains=query) |
            Q(foglio__icontains=query) |
            Q(mappale__icontains=query) |
            Q(subalterno__icontains=query) |
            Q(cliente__nome__icontains=query)
        )

        pratiche = Pratica.objects.filter(
            studio=studio
        ).filter(
            Q(oggetto__icontains=query) |
            Q(comune__icontains=query) |
            Q(protocollo__icontains=query) |
            Q(cliente__nome__icontains=query)
        )

        scadenze = Scadenza.objects.filter(
            pratica__studio=studio
        ).filter(
            Q(titolo__icontains=query) |
            Q(descrizione__icontains=query)
        )

        documenti = Documento.objects.filter(
            pratica__studio=studio
        ).filter(
            Q(titolo__icontains=query) |
            Q(note__icontains=query)
        )

    return render(
        request,
        'dashboard/ricerca.html',
        {
            'query': query,
            'clienti': clienti,
            'immobili': immobili,
            'pratiche': pratiche,
            'scadenze': scadenze,
            'documenti': documenti,
        }
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