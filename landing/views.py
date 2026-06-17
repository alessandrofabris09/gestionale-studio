from django.http import HttpResponse
from django.shortcuts import render, redirect

from workflow.models import TipoWorkflow


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    return render(request, 'landing/home.html')


def privacy_policy(request):
    return render(request, 'landing/privacy.html')


def termini_utilizzo(request):
    return render(request, 'landing/termini.html')


def carica_tipi_pratica(request, codice):
    """
    Funzione temporanea.
    Carica automaticamente i tipi pratica standard nel nuovo database.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'CARICA-TIPI-PRATICA-2026'

    if codice != CODICE_SICUREZZA:
        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    tipi_pratica = [
        'CILA',
        'SCIA',
        'Permesso di Costruire',
        'Autorizzazione Paesaggistica',
        'Compatibilità Paesaggistica',
        'Sanatoria edilizia',
        'Accertamento di conformità',
        'Agibilità',
        'Comunicazione fine lavori',
        'Pratica catastale',
        'DOCFA',
        'PREGEO',
        'Frazionamento',
        'Tipo mappale',
        'Voltura catastale',
        'Successione',
        'Perizia tecnica',
        'Relazione tecnica',
        'Relazione paesaggistica',
        'Computo metrico',
        'Direzione lavori',
        'Sicurezza cantiere',
        'Accesso atti',
        'APE',
        'ENEA',
        'Altro',
    ]

    creati = []
    gia_presenti = []

    for nome in tipi_pratica:

        workflow, created = TipoWorkflow.objects.get_or_create(
            nome=nome,
            defaults={
                'attivo': True,
            }
        )

        if not workflow.attivo:
            workflow.attivo = True
            workflow.save()

        if created:
            creati.append(nome)
        else:
            gia_presenti.append(nome)

    testo = 'Caricamento tipi pratica completato.\n\n'

    testo += f'Creati: {len(creati)}\n'
    for nome in creati:
        testo += f'- {nome}\n'

    testo += f'\nGià presenti: {len(gia_presenti)}\n'
    for nome in gia_presenti:
        testo += f'- {nome}\n'

    testo += '\nOra controlla la tendina in Pratiche.'

    return HttpResponse(
        testo,
        content_type='text/plain'
    )