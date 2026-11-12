from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, F, OuterRef, Q, Subquery, Value, When
from django.shortcuts import render, redirect
from django.utils.timezone import now, localdate

from studi.utils import (
    get_studio_utente,
    is_admin_piattaforma,
    studio_deve_upgrade,
    studio_puo_creare_pratiche,
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
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
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
        is_admin_piattaforma(request) or
        puo_creare_pratiche(request) or
        puo_gestire_documenti(request)
    )


@login_required
def home(request):

    studio = get_studio_sicuro(request)

    if not studio and not is_admin_piattaforma(request):
        logout(request)
        return redirect('login')

    if studio and studio_deve_upgrade(studio):
        return redirect('abbonamento')

    if is_admin_piattaforma(request) and not studio:
        pratiche = Pratica.objects.all()
        scadenze = Scadenza.objects.filter(archiviata=False)
        parcelle = Parcella.objects.all()
        eventi = EventoAgenda.objects.all()
        attivita_qs = Attivita.objects.all()

    else:
        pratiche = Pratica.objects.filter(
            studio=studio
        )

        scadenze = Scadenza.objects.filter(
            archiviata=False,
            pratica__studio=studio
        )

        parcelle = Parcella.objects.filter(
            pratica__studio=studio
        )

        eventi = EventoAgenda.objects.filter(
            studio=studio
        )

        attivita_qs = Attivita.objects.filter(
            pratica__studio=studio
        )

    puo_vedere_pratiche = puo_vedere_area_pratiche(request)
    pratiche_operative = None
    if puo_vedere_pratiche:
        prima_scadenza = scadenze.filter(
            pratica_id=OuterRef('pk'), completata=False,
        ).annotate(
            ordine_priorita=Case(
                When(priorita='ALTA', then=Value(0)),
                When(priorita='MEDIA', then=Value(1)),
                default=Value(2),
            ),
        ).order_by('data_scadenza', 'ordine_priorita', 'pk')
        aperte = pratiche.exclude(stato='CONCLUSA').select_related('cliente').annotate(
            scadenza_operativa=Subquery(prima_scadenza.values('data_scadenza')[:1]),
            priorita_operativa=Subquery(prima_scadenza.values('priorita')[:1]),
            ordine_priorita=Subquery(prima_scadenza.values('ordine_priorita')[:1]),
        ).order_by(
            F('scadenza_operativa').asc(nulls_last=True),
            F('ordine_priorita').asc(nulls_last=True),
            'pk',
        )
        pratiche_operative = Paginator(aperte, 12).get_page(request.GET.get('operative'))

    attivita_recenti = attivita_qs.select_related(
        'utente',
        'pratica'
    ).order_by('-data')[:10]

    scadenze_imminenti = scadenze.filter(
        data_scadenza__gte=localdate(),
        data_scadenza__lte=localdate() + timedelta(days=7),
        completata=False
    ).count()

    totale_parcelle = totale_incassato = totale_da_incassare = Decimal('0.00')
    parcelle_scadute = 0
    oggi = localdate()
    puo_vedere_economia = puo_vedere_parcelle(request)
    if puo_vedere_economia:
        for parcella in parcelle.exclude(tipo_documento='PREVENTIVO').iterator():
            pagato = parcella.importo_pagato
            residuo = parcella.saldo_residuo
            totale_parcelle += pagato + residuo
            totale_incassato += pagato
            if residuo > 0:
                totale_da_incassare += residuo
                if parcella.data_scadenza and parcella.data_scadenza < oggi:
                    parcelle_scadute += 1

    ultime_parcelle = parcelle.order_by('-id')[:5]

    ultime_pratiche = pratiche.order_by('-id')[:5]

    ultime_scadenze = scadenze.filter(
        completata=False, data_scadenza__gte=localdate(),
    ).order_by('data_scadenza', 'pk')[:5]

    eventi_oggi = eventi.filter(
        data=now().date(),
        completato=False
    ).order_by(
        'ora_inizio'
    )[:5]

    notifiche = []

    if puo_vedere_economia:
        if parcelle_scadute:
            notifiche.append({
                'tipo': 'danger',
                'icona': 'fa-file-invoice-dollar',
                'titolo': 'Parcelle scadute',
                'testo': f'Hai {parcelle_scadute} parcelle scadute da incassare.',
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

        'puo_vedere_pratiche': puo_vedere_pratiche,
        'mostra_prima_pratica': (
            studio is not None
            and puo_creare_pratiche(request)
            and not pratiche.exists()
            and studio_puo_creare_pratiche(studio)
        ),
        'pratiche_operative': pratiche_operative,
        'oggi': localdate(),
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

    if not studio and not is_admin_piattaforma(request):
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

        if is_admin_piattaforma(request) and not studio:

            clienti_base = Cliente.objects.all()
            immobili_base = Immobile.objects.all()
            pratiche_base = Pratica.objects.all()
            scadenze_base = Scadenza.objects.filter(archiviata=False)
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
                archiviata=False,
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
    """Compatibilita con il vecchio indirizzo, senza creare backup incompleti."""
    if not puo_gestire_backup(request):
        return accesso_negato(request)
    return redirect('lista_backup')


def privacy_policy(request):
    return render(request, "landing/privacy.html")

def cookie_policy(request):
    return render(request, "landing/cookie.html")

def termini(request):
    return render(request, "landing/termini.html")
