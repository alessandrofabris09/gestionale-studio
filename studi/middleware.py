from django.shortcuts import render

from .utils import get_studio_utente

# Durante l’esportazione rimangono disponibili solo viste di consultazione note.
LETTURA_BETA = frozenset({
    'home', 'ricerca_globale', 'profilo_studio', 'utenti_studio', 'lista_utenti',
    'lista_pratiche', 'dettaglio_pratica', 'pdf_pratica', 'lista_ore_pratica',
    'lista_clienti', 'dettaglio_cliente', 'lista_immobili', 'dettaglio_immobile',
    'lista_documenti', 'lista_agenda', 'agenda_oggi', 'lista_scadenze',
    'calendario_scadenze', 'eventi_calendario', 'lista_parcelle', 'pdf_parcella',
    'storico_incassi', 'modelli_workflow', 'esporta_beta',
})
SEMPRE_DISPONIBILI = frozenset({
    'abbonamento', 'privacy_policy', 'cookie_policy', 'termini',
    'login', 'logout', 'accounts_login', 'accounts_logout',
    'password_reset', 'password_reset_done', 'password_reset_confirm', 'password_reset_complete',
    'stripe_webhook',
})


class AccessoBetaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        nome = request.resolver_match.url_name
        if nome in SEMPRE_DISPONIBILI or not request.user.is_authenticated:
            return None

        studio = get_studio_utente(request)
        fase = studio.fase_beta() if studio else None
        request.fase_beta = fase
        if fase not in ('LETTURA', 'CHIUSA'):
            return None
        if fase == 'LETTURA' and nome in LETTURA_BETA and request.method in ('GET', 'HEAD'):
            return None
        if fase == 'LETTURA' and nome == 'esporta_beta' and request.method == 'POST':
            return None

        return render(request, 'studi/beta_bloccata.html', {'fase_beta': fase}, status=403)
