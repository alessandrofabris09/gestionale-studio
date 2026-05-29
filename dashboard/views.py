import shutil

from pathlib import Path
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.utils.timezone import now

from workflow.models import FasePratica, ChecklistPratica

from studi.utils import (
    get_studio_utente,
    studio_deve_upgrade,
)

from studi.permessi import (
    puo_gestire_backup,
    puo_gestire_documenti,
    puo_vedere_parcelle,
    puo_usare_agenda,
    puo_creare_pratiche,
)

from clienti.models import Cliente
from immobili.models import Immobile
from pratiche.models import Pratica
from scadenze.models import Scadenza
from documenti.models import Documento
from parcelle.models import Parcella
from agenda.models import EventoAgenda
from attivita.models import Attivita


def accesso_negato(request):
    """
    Pagina semplice di blocco accesso.
    """

    return HttpResponseForbidden(
        """
        <h1>Accesso negato</h1>
        <p>Non hai i permessi per accedere a questa sezione.</p>
        <p><a href="/dashboard/">Torna alla dashboard</a></p>
        """
    )


def get_studio_sicuro(request):
    """
    Recupera lo studio dell'utente senza mandare in errore la view.
    """

    try:
        return get_studio_utente(request)
    except Exception:
        return None


def puo_vedere_area_pratiche(request):
    """
    Area pratiche/clienti/immobili/documenti visibile a chi può
    creare pratiche oppure gestire documenti.
    """

    return (
        request.user.is_superuser or
        puo_creare_pratiche(request) or
        puo_gestire_documenti(request)
    )


@login_required
def home(request):

    studio = get_studio_sicuro(request)

    if not studio and not request.user.is_superuser:
        logout(request)
        return redirect('login')

    if studio and studio_deve_upgrade(studio):
        return redirect('abbonamento')

    if request.user.is_superuser and not studio:
        pratiche = Pratica.objects.all()
        scadenze = Scadenza.objects.all()
        parcelle = Parcella.objects.all()
        eventi = EventoAgenda.objects.all()
        clienti_qs = Cliente.objects.all()
        immobili_qs = Immobile.objects.all()
        attivita_qs = Attivita.objects.all()
        fasi_qs = FasePratica.objects.all()
        checklist_qs = ChecklistPratica.objects.all()

    else:
        pratiche = Pratica.objects.filter(
            studio=studio
        )

        scadenze = Scadenza.objects.filter(
            pratica__studio=studio
        )

        parcelle = Parcella.objects.filter(
            pratica__studio=studio
        )

        eventi = EventoAgenda.objects.filter(
            studio=studio
        )

        clienti_qs = Cliente.objects.filter(
            studio=studio
        )

        immobili_qs = Immobile.objects.filter(
            studio=studio
        )

        attivita_qs = Attivita.objects.filter(
            pratica__studio=studio
        )

        fasi_qs = FasePratica.objects.filter(
            workflow_pratica__pratica__studio=studio
        )

        checklist_qs = ChecklistPratica.objects.filter(
            workflow_pratica__pratica__studio=studio
        )

    pratiche_aperte = pratiche.exclude(
        stato='CONCLUSA'
    ).count()

    pratiche_chiuse = pratiche.filter(
        stato='CONCLUSA'
    ).count()

    attivita_recenti = attivita_qs.select_related(
        'utente',
        'pratica'
    ).order_by('-data')[:10]

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

    oggi = now().date()

    notifiche = []

    if puo_vedere_parcelle(request):

        parcelle_scadute_qs = parcelle.filter(
            stato='DA_PAGARE',
            data_scadenza__lt=oggi
        )

        if parcelle_scadute_qs.exists():
            notifiche.append({
                'tipo': 'danger',
                'icona': 'fa-file-invoice-dollar',
                'titolo': 'Parcelle scadute',
                'testo': f'Hai {parcelle_scadute_qs.count()} parcelle scadute da incassare.',
                'link': '/parcelle/',
            })

    if puo_usare_agenda(request):

        scadenze_urgenti_qs = scadenze.filter(
            completata=False,
            data_scadenza__gte=oggi,
            data_scadenza__lte=oggi + timedelta(days=7)
        )

        if scadenze_urgenti_qs.exists():
            notifiche.append({
                'tipo': 'warning',
                'icona': 'fa-clock',
                'titolo': 'Scadenze imminenti',
                'testo': f'Hai {scadenze_urgenti_qs.count()} scadenze nei prossimi 7 giorni.',
                'link': '/scadenze/alert/',
            })

        eventi_oggi_qs = eventi.filter(
            data=oggi,
            completato=False
        )

        if eventi_oggi_qs.exists():
            notifiche.append({
                'tipo': 'success',
                'icona': 'fa-calendar-day',
                'titolo': 'Agenda di oggi',
                'testo': f'Hai {eventi_oggi_qs.count()} eventi in agenda oggi.',
                'link': '/agenda/oggi/',
            })

    if puo_vedere_area_pratiche(request):

        fasi_scadute_qs = fasi_qs.filter(
            completata=False,
            data_scadenza__lt=oggi
        )

        if fasi_scadute_qs.exists():
            notifiche.append({
                'tipo': 'danger',
                'icona': 'fa-diagram-project',
                'titolo': 'Workflow in ritardo',
                'testo': f'Hai {fasi_scadute_qs.count()} fasi workflow scadute.',
                'link': '/pratiche/',
            })

        checklist_incomplete_qs = checklist_qs.filter(
            obbligatorio=True,
            completato=False
        )

        if checklist_incomplete_qs.exists():
            notifiche.append({
                'tipo': 'info',
                'icona': 'fa-list-check',
                'titolo': 'Checklist incomplete',
                'testo': f'Hai {checklist_incomplete_qs.count()} voci obbligatorie ancora da completare.',
                'link': '/pratiche/',
            })

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

        'tot_clienti': clienti_qs.count(),
        'tot_immobili': immobili_qs.count(),
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

        'attivita_recenti': attivita_recenti,

        'notifiche': notifiche,
    }

    return render(
        request,
        'dashboard/home.html',
        context
    )


@login_required
def ricerca_globale(request):

    studio = get_studio_sicuro(request)

    if not studio and not request.user.is_superuser:
        logout(request)
        return redirect('login')

    query = request.GET.get('q', '')

    clienti = []
    immobili = []
    pratiche = []
    scadenze = []
    documenti = []
    parcelle = []
    eventi = []

    if query:

        if request.user.is_superuser and not studio:

            clienti_base = Cliente.objects.all()
            immobili_base = Immobile.objects.all()
            pratiche_base = Pratica.objects.all()
            scadenze_base = Scadenza.objects.all()
            documenti_base = Documento.objects.all()
            parcelle_base = Parcella.objects.all()
            eventi_base = EventoAgenda.objects.all()

        else:

            clienti_base = Cliente.objects.filter(
                studio=studio
            )

            immobili_base = Immobile.objects.filter(
                studio=studio
            )

            pratiche_base = Pratica.objects.filter(
                studio=studio
            )

            scadenze_base = Scadenza.objects.filter(
                pratica__studio=studio
            )

            documenti_base = Documento.objects.filter(
                pratica__studio=studio
            )

            parcelle_base = Parcella.objects.filter(
                pratica__studio=studio
            )

            eventi_base = EventoAgenda.objects.filter(
                studio=studio
            )

        if puo_vedere_area_pratiche(request):

            clienti = clienti_base.filter(
                Q(nome__icontains=query) |
                Q(email__icontains=query) |
                Q(telefono__icontains=query) |
                Q(codice_fiscale__icontains=query) |
                Q(partita_iva__icontains=query)
            )

            immobili = immobili_base.filter(
                Q(comune__icontains=query) |
                Q(indirizzo__icontains=query) |
                Q(foglio__icontains=query) |
                Q(mappale__icontains=query) |
                Q(subalterno__icontains=query) |
                Q(cliente__nome__icontains=query)
            )

            pratiche = pratiche_base.filter(
                Q(oggetto__icontains=query) |
                Q(comune__icontains=query) |
                Q(protocollo__icontains=query) |
                Q(cliente__nome__icontains=query)
            )

        if puo_usare_agenda(request):

            scadenze = scadenze_base.filter(
                Q(titolo__icontains=query) |
                Q(descrizione__icontains=query)
            )

            eventi = eventi_base.filter(
                Q(titolo__icontains=query) |
                Q(descrizione__icontains=query)
            )

        if puo_gestire_documenti(request):

            documenti = documenti_base.filter(
                Q(titolo__icontains=query) |
                Q(note__icontains=query)
            )

        if puo_vedere_parcelle(request):

            parcelle = parcelle_base.filter(
                Q(descrizione__icontains=query) |
                Q(note__icontains=query) |
                Q(pratica__oggetto__icontains=query)
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
            'parcelle': parcelle,
            'eventi': eventi,
        }
    )


@login_required
def backup_manuale(request):

    if not puo_gestire_backup(request):
        return accesso_negato(request)

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