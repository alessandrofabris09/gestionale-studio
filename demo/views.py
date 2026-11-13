from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_safe

from .models import VERSIONE_CONSENSO, RichiestaPro

SITO_UFFICIALE = 'https://studiotecnicocloud.it/'


@require_safe
def home(request):
    return redirect(SITO_UFFICIALE, permanent=True)


@require_safe
def prova(request):
    return redirect(SITO_UFFICIALE + '#funzionalita', permanent=True)


@require_safe
def lista(request):
    return redirect(SITO_UFFICIALE + '#lancio-beta', permanent=True)


@never_cache
@require_http_methods(['GET', 'POST'])
def conferma(request, token):
    return render(request, 'demo/esito.html', {
        'titolo': 'La beta PRO si è spostata',
        'testo': 'Per partecipare al lancio, registra il tuo studio Free dalla pagina ufficiale.',
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
    return render(request, 'demo/termini.html')
