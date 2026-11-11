import logging
import uuid
from datetime import timedelta

from anymail.exceptions import AnymailError
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from gestionale.beta_pro import (
    GIORNI_ESPORTAZIONE_BETA,
    GIORNI_PREAVVISO_BETA,
    MESI_BETA,
    POSTI_BETA,
    QUOTA_BETA_MB,
)

from .forms import RichiestaProForm
from .models import DURATA_CONSENSO, DURATA_RICHIESTA, OBIETTIVO_PRO, VERSIONE_CONSENSO, RichiestaPro

logger = logging.getLogger(__name__)
ATTESA_REINVIO = timedelta(minutes=15)
ESEMPI_PRATICHE = {
    'cila': {
        'modello': 'CILA',
        'checklist': [
            'Delega e dati dei soggetti', 'Titoli edilizi di riferimento',
            'Elaborati ante e post operam', 'Ricevuta del deposito',
        ],
    },
    'docfa': {
        'modello': 'DOCFA - nuova costruzione',
        'checklist': [
            'Estremi del tipo mappale', 'Planimetrie delle unità',
            'Elaborato planimetrico ed elenco subalterni se pertinenti', 'Ricevuta catastale',
        ],
    },
}


def _contesto_pro():
    return {
        'obiettivo': OBIETTIVO_PRO,
        'totale': RichiestaPro.confermate_attive().count(),
        **_condizioni_beta(),
    }


def _condizioni_beta():
    return {
        'posti_beta': POSTI_BETA,
        'mesi_beta': MESI_BETA,
        'quota_beta_mb': QUOTA_BETA_MB,
        'giorni_preavviso_beta': GIORNI_PREAVVISO_BETA,
        'giorni_esportazione_beta': GIORNI_ESPORTAZIONE_BETA,
    }


def _limite_raggiunto(chiave, massimo, secondi):
    cache.add(chiave, 0, timeout=secondi)
    try:
        return cache.incr(chiave) > massimo
    except ValueError:
        return True


def _invia_conferma(richiesta):
    link = settings.DEMO_SITE_URL + reverse('demo_conferma', args=[richiesta.token])
    revoca = settings.DEMO_SITE_URL + reverse('demo_ritira', args=[richiesta.token_revoca])
    return send_mail(
        'Conferma la candidatura alla beta PRO di Studio Tecnico Cloud',
        'Hai inviato una candidatura per la beta PRO di Studio Tecnico Cloud. '
        f'Per confermare entro 24 ore, apri questo link e premi Conferma:\n{link}\n\n'
        f'Per annullare la richiesta:\n{revoca}\n\n'
        'Se non hai effettuato la richiesta, puoi ignorare questa email.',
        settings.DEFAULT_FROM_EMAIL,
        [richiesta.email],
    )


@require_GET
def home(request):
    return render(request, 'demo/home.html', {
        **_contesto_pro(), 'esempio': ESEMPI_PRATICHE['cila'],
    })


@require_GET
def prova(request):
    return render(request, 'demo/prova.html', {
        'esempi': ESEMPI_PRATICHE, 'esempio': ESEMPI_PRATICHE['cila'],
    })


@never_cache
@require_http_methods(['GET', 'POST'])
def lista(request):
    form = RichiestaProForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        # Contatori temporanei. L'indirizzo IP non viene salvato nella lista.
        ip = request.META.get('REMOTE_ADDR', '')
        if settings.ON_RENDER:
            # Render termina la connessione e aggiunge l'IP all'estremità della catena.
            ip = request.META.get('HTTP_X_FORWARDED_FOR', ip).split(',')[-1].strip()
        chiave = salted_hmac('demo-lista-pro', ip).hexdigest()
        if _limite_raggiunto(f'demo-pro-ip-{chiave}', 8, 600) or _limite_raggiunto('demo-pro-totale', 40, 600):
            return render(request, 'demo/esito.html', {
                'titolo': 'Troppe richieste',
                'testo': 'Attendi qualche minuto e riprova.',
            }, status=429)

        if form.is_valid():
            now = timezone.now()
            richiesta, creata = RichiestaPro.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={'versione_consenso': VERSIONE_CONSENSO, 'richiesta_il': now},
            )
            if richiesta.confermata_il:
                scaduta = richiesta.confermata_il <= now - DURATA_CONSENSO
            else:
                scaduta = richiesta.richiesta_il <= now - ATTESA_REINVIO
            if not creata and (scaduta or richiesta.versione_consenso != VERSIONE_CONSENSO):
                token = uuid.uuid4()
                creata = bool(RichiestaPro.objects.filter(
                    pk=richiesta.pk, confermata_il=richiesta.confermata_il, token=richiesta.token,
                ).update(token=token, richiesta_il=now, confermata_il=None, versione_consenso=VERSIONE_CONSENSO))
                richiesta.token = token

            if creata:
                try:
                    inviata = _invia_conferma(richiesta)
                except (AnymailError, OSError) as exc:
                    logger.warning('Invio conferma PRO non riuscito (%s)', type(exc).__name__)
                    inviata = False
                if not inviata:
                    # Mantiene la pausa tra tentativi anche durante un disservizio del fornitore.
                    return render(request, 'demo/esito.html', {
                        'titolo': 'Invio temporaneamente indisponibile',
                        'testo': 'Riprova tra almeno 15 minuti.',
                    }, status=503)
            return redirect(reverse('demo_lista') + '?richiesta=inviata')

    return render(request, 'demo/lista.html', {
        **_contesto_pro(), 'form': form, 'inviata': request.GET.get('richiesta') == 'inviata',
    })


@never_cache
@require_http_methods(['GET', 'POST'])
def conferma(request, token):
    if request.method == 'GET':
        return render(request, 'demo/azione.html', {'titolo': 'Conferma la candidatura', 'azione': 'Conferma'})
    now = timezone.now()
    confermata = RichiestaPro.objects.filter(
        token=token, versione_consenso=VERSIONE_CONSENSO,
        confermata_il__isnull=True, richiesta_il__gt=now - DURATA_RICHIESTA,
    ).update(confermata_il=now)
    if confermata or RichiestaPro.confermate_attive().filter(token=token).exists():
        return render(request, 'demo/esito.html', {
            'titolo': 'Candidatura confermata',
            'testo': 'Ti contatteremo via email per comunicarti l’esito. La prova partirà solo dopo l’attivazione dello studio.',
        })
    return render(request, 'demo/esito.html', {
        'titolo': 'Link scaduto o non valido',
        'testo': 'Puoi fare una nuova richiesta dalla pagina del piano PRO.',
    }, status=410)


@never_cache
@require_http_methods(['GET', 'POST'])
def ritira(request, token):
    if request.method == 'GET':
        return render(request, 'demo/azione.html', {'titolo': 'Ritira la richiesta', 'azione': 'Ritira la richiesta'})
    RichiestaPro.objects.filter(token_revoca=token).delete()
    return render(request, 'demo/esito.html', {
        'titolo': 'Richiesta rimossa',
        'testo': 'L’indirizzo non è più nella lista per il piano PRO.',
    })


@require_GET
def privacy(request):
    return render(request, 'demo/privacy.html', {'versione_consenso': VERSIONE_CONSENSO})


@require_GET
def cookie(request):
    return render(request, 'demo/cookie.html')


@require_GET
def termini(request):
    return render(request, 'demo/termini.html', {'obiettivo': OBIETTIVO_PRO, **_condizioni_beta()})
