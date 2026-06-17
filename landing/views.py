from django.http import HttpResponse
from django.shortcuts import render, redirect

from workflow.models import (
    TipoWorkflow,
    FaseWorkflow,
    ChecklistWorkflow,
)


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    return render(request, 'landing/home.html')


def privacy_policy(request):
    return render(request, 'landing/privacy.html')


def termini_utilizzo(request):
    return render(request, 'landing/termini.html')


def carica_workflow_base(request, codice):
    """
    Funzione temporanea.
    Carica automaticamente workflow, fasi e checklist nel nuovo database.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'CARICA-WORKFLOW-BASE-2026'

    if codice != CODICE_SICUREZZA:
        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    workflow_data = [
        {
            'nome': 'Accesso atti',
            'categoria': 'EDILIZIA',
            'descrizione': 'Procedimento per richiesta e gestione accesso agli atti presso enti pubblici.',
            'fasi': [
                'Raccolta incarico e dati richiedente',
                'Predisposizione delega e documenti',
                'Invio richiesta all’ente competente',
                'Monitoraggio evasione richiesta',
                'Ricezione e verifica documentazione',
                'Consegna documenti al cliente',
            ],
            'checklist': [
                'Documento identità richiedente',
                'Codice fiscale richiedente',
                'Delega accesso atti firmata',
                'Titolo di proprietà o visura catastale',
                'Modulo richiesta accesso atti',
                'Ricevuta pagamento diritti di segreteria',
                'Documentazione ricevuta dall’ente',
            ],
        },
        {
            'nome': 'CILA',
            'categoria': 'EDILIZIA',
            'descrizione': 'Comunicazione Inizio Lavori Asseverata per interventi edilizi minori.',
            'fasi': [
                'Sopralluogo e verifica stato di fatto',
                'Raccolta documentazione urbanistica e catastale',
                'Redazione elaborati grafici',
                'Redazione relazione tecnica asseverata',
                'Compilazione modulistica comunale',
                'Invio pratica al Comune',
                'Gestione integrazioni',
                'Fine lavori e archiviazione pratica',
            ],
            'checklist': [
                'Documento identità committente',
                'Codice fiscale committente',
                'Titolo di proprietà',
                'Estratto mappa catastale',
                'Visura catastale',
                'Planimetria catastale',
                'Elaborati stato di fatto',
                'Elaborati stato di progetto',
                'Relazione tecnica asseverata',
                'Modulo CILA',
                'Ricevuta diritti di segreteria',
                'Impresa esecutrice e DURC se necessario',
            ],
        },
        {
            'nome': 'SCIA',
            'categoria': 'EDILIZIA',
            'descrizione': 'Segnalazione Certificata di Inizio Attività.',
            'fasi': [
                'Sopralluogo e analisi intervento',
                'Verifica conformità urbanistica',
                'Redazione progetto',
                'Redazione asseverazione tecnica',
                'Raccolta allegati obbligatori',
                'Invio SCIA',
                'Gestione eventuali richieste integrazione',
                'Comunicazione fine lavori',
            ],
            'checklist': [
                'Documento identità committente',
                'Titolo di proprietà',
                'Visura catastale',
                'Planimetria catastale',
                'Estratto mappa',
                'Elaborati grafici',
                'Relazione tecnica asseverata',
                'Modulo SCIA',
                'Documentazione impresa',
                'DURC',
                'Ricevuta diritti',
                'Fine lavori',
            ],
        },
        {
            'nome': 'Permesso di Costruire',
            'categoria': 'EDILIZIA',
            'descrizione': 'Procedimento edilizio per nuova costruzione o interventi soggetti a PDC.',
            'fasi': [
                'Verifica urbanistica preliminare',
                'Sopralluogo e rilievo',
                'Studio progettuale',
                'Redazione elaborati grafici',
                'Relazione tecnica illustrativa',
                'Raccolta pareri e nulla osta',
                'Presentazione istanza',
                'Gestione istruttoria comunale',
                'Rilascio titolo edilizio',
                'Comunicazione inizio lavori',
            ],
            'checklist': [
                'Documento identità committente',
                'Titolo di proprietà',
                'Estratto mappa',
                'Visura catastale',
                'CTR / estratti urbanistici',
                'Elaborati grafici completi',
                'Relazione tecnica illustrativa',
                'Calcolo superfici e volumi',
                'Verifica parcheggi',
                'Documentazione energetica se dovuta',
                'Pareri enti competenti',
                'Ricevuta diritti di segreteria',
            ],
        },
        {
            'nome': 'Autorizzazione Paesaggistica',
            'categoria': 'AMBIENTE',
            'descrizione': 'Pratica per interventi in area soggetta a vincolo paesaggistico.',
            'fasi': [
                'Verifica vincolo paesaggistico',
                'Sopralluogo e documentazione fotografica',
                'Raccolta estratti cartografici',
                'Redazione relazione paesaggistica',
                'Predisposizione elaborati grafici',
                'Invio istanza paesaggistica',
                'Gestione istruttoria e integrazioni',
                'Ricezione autorizzazione',
            ],
            'checklist': [
                'Documento identità richiedente',
                'Titolo di proprietà',
                'Estratto mappa catastale',
                'Ortofoto',
                'Estratto vincoli',
                'Estratto PRG / PI',
                'CTR',
                'Documentazione fotografica',
                'Coni visuali fotografici',
                'Elaborati stato di fatto',
                'Elaborati stato di progetto',
                'Relazione paesaggistica',
                'Fotoinserimento se necessario',
            ],
        },
        {
            'nome': 'Compatibilità Paesaggistica',
            'categoria': 'AMBIENTE',
            'descrizione': 'Accertamento di compatibilità paesaggistica per opere già eseguite.',
            'fasi': [
                'Verifica opere eseguite',
                'Verifica vincolo paesaggistico',
                'Raccolta documentazione fotografica',
                'Redazione relazione di compatibilità',
                'Predisposizione elaborati grafici',
                'Presentazione istanza',
                'Gestione istruttoria',
                'Rilascio provvedimento',
            ],
            'checklist': [
                'Documento identità richiedente',
                'Titolo di proprietà',
                'Estratto mappa',
                'Estratto vincoli',
                'Documentazione fotografica',
                'Elaborati stato autorizzato',
                'Elaborati stato rilevato',
                'Relazione di compatibilità paesaggistica',
                'Ricevuta diritti',
            ],
        },
        {
            'nome': 'DOCFA',
            'categoria': 'CATASTO',
            'descrizione': 'Pratica catastale DOCFA per nuova costruzione, variazione o unità immobiliari urbane.',
            'fasi': [
                'Raccolta documentazione catastale',
                'Rilievo immobile',
                'Predisposizione planimetrie catastali',
                'Compilazione DOCFA',
                'Controllo rendita e classamento',
                'Invio telematico',
                'Verifica ricevute catastali',
                'Consegna elaborati al cliente',
            ],
            'checklist': [
                'Documento identità intestatario',
                'Codice fiscale intestatario',
                'Titolo di proprietà',
                'Visura catastale',
                'Planimetria precedente',
                'Elaborato planimetrico se presente',
                'Rilievo aggiornato',
                'Planimetria catastale nuova',
                'File DOCFA',
                'Ricevuta presentazione',
                'Ricevuta approvazione',
            ],
        },
        {
            'nome': 'PREGEO',
            'categoria': 'CATASTO',
            'descrizione': 'Pratica catastale PREGEO per frazionamenti, tipi mappali e aggiornamenti cartografici.',
            'fasi': [
                'Raccolta documentazione catastale',
                'Rilievo topografico',
                'Elaborazione libretto misure',
                'Predisposizione proposta di aggiornamento',
                'Compilazione PREGEO',
                'Invio telematico',
                'Verifica approvazione',
                'Consegna atti al cliente',
            ],
            'checklist': [
                'Documento identità intestatario',
                'Titolo di proprietà',
                'Estratto mappa',
                'Visure catastali',
                'Monografie punti fiduciali',
                'Libretto misure',
                'Proposta di aggiornamento',
                'Relazione tecnica',
                'File PREGEO',
                'Ricevuta invio',
                'Approvazione Agenzia Entrate',
            ],
        },
        {
            'nome': 'Frazionamento',
            'categoria': 'CATASTO',
            'descrizione': 'Frazionamento catastale di terreni o aree.',
            'fasi': [
                'Verifica mappa e proprietà',
                'Rilievo topografico',
                'Definizione nuove dividenti',
                'Predisposizione tipo di frazionamento',
                'Invio PREGEO',
                'Approvazione catastale',
                'Consegna elaborati',
            ],
            'checklist': [
                'Titolo di proprietà',
                'Estratto mappa',
                'Visure catastali',
                'Documento intestatari',
                'Rilievo topografico',
                'Libretto PREGEO',
                'Tipo di frazionamento',
                'Ricevuta approvazione',
            ],
        },
        {
            'nome': 'Voltura catastale',
            'categoria': 'CATASTO',
            'descrizione': 'Voltura catastale per aggiornamento intestazioni.',
            'fasi': [
                'Raccolta atto o dichiarazione',
                'Verifica intestazioni catastali',
                'Compilazione voltura',
                'Invio pratica',
                'Verifica aggiornamento visure',
            ],
            'checklist': [
                'Atto notarile o successione',
                'Documento identità',
                'Codice fiscale',
                'Visure catastali',
                'Modulo voltura',
                'Ricevuta invio',
                'Visura aggiornata',
            ],
        },
        {
            'nome': 'Successione',
            'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
            'descrizione': 'Dichiarazione di successione e adempimenti catastali collegati.',
            'fasi': [
                'Raccolta dati eredi',
                'Raccolta documentazione immobili',
                'Verifica attivo ereditario',
                'Compilazione dichiarazione successione',
                'Calcolo imposte',
                'Invio dichiarazione',
                'Volture catastali',
                'Consegna ricevute',
            ],
            'checklist': [
                'Certificato di morte',
                'Documenti eredi',
                'Codici fiscali eredi',
                'Dichiarazione sostitutiva atto notorio',
                'Visure catastali',
                'Atti di proprietà',
                'Estratti conti correnti se necessari',
                'Prospetto imposte',
                'Ricevuta invio successione',
                'Volture catastali',
            ],
        },
        {
            'nome': 'APE',
            'categoria': 'ENERGIA',
            'descrizione': 'Attestato di Prestazione Energetica.',
            'fasi': [
                'Raccolta dati immobile',
                'Sopralluogo obbligatorio',
                'Raccolta dati impianti',
                'Elaborazione software energetico',
                'Redazione APE',
                'Deposito al catasto energetico',
                'Consegna attestato',
            ],
            'checklist': [
                'Documento proprietario',
                'Visura catastale',
                'Planimetria catastale',
                'Libretto impianto',
                'Dati generatore',
                'Dati serramenti',
                'Foto immobile',
                'File APE',
                'Ricevuta deposito regionale',
            ],
        },
        {
            'nome': 'ENEA',
            'categoria': 'ENERGIA',
            'descrizione': 'Comunicazione ENEA per interventi di risparmio energetico o bonus casa.',
            'fasi': [
                'Raccolta dati committente',
                'Raccolta fatture e bonifici',
                'Verifica interventi agevolabili',
                'Raccolta schede tecniche',
                'Compilazione portale ENEA',
                'Invio comunicazione',
                'Consegna ricevuta CPID',
            ],
            'checklist': [
                'Documento committente',
                'Codice fiscale committente',
                'Dati catastali immobile',
                'Fatture interventi',
                'Bonifici parlanti',
                'Schede tecniche prodotti',
                'Asseverazioni o dichiarazioni se dovute',
                'Data fine lavori',
                'Ricevuta ENEA / CPID',
            ],
        },
        {
            'nome': 'Perizia tecnica',
            'categoria': 'ALTRO',
            'descrizione': 'Perizia tecnica estimativa o descrittiva.',
            'fasi': [
                'Conferimento incarico',
                'Sopralluogo',
                'Raccolta documentazione',
                'Analisi tecnica',
                'Redazione perizia',
                'Revisione finale',
                'Consegna al cliente',
            ],
            'checklist': [
                'Incarico professionale',
                'Documento cliente',
                'Documentazione catastale',
                'Documentazione urbanistica',
                'Fotografie',
                'Elaborati grafici se necessari',
                'Perizia firmata',
            ],
        },
        {
            'nome': 'Relazione tecnica',
            'categoria': 'ALTRO',
            'descrizione': 'Relazione tecnica descrittiva o illustrativa.',
            'fasi': [
                'Raccolta dati intervento',
                'Sopralluogo',
                'Verifica documentazione',
                'Redazione relazione',
                'Controllo finale',
                'Consegna o allegazione alla pratica',
            ],
            'checklist': [
                'Dati committente',
                'Documentazione fotografica',
                'Estratti cartografici se necessari',
                'Elaborati grafici',
                'Relazione tecnica firmata',
            ],
        },
        {
            'nome': 'Relazione paesaggistica',
            'categoria': 'AMBIENTE',
            'descrizione': 'Relazione paesaggistica ordinaria o semplificata.',
            'fasi': [
                'Analisi vincoli',
                'Sopralluogo e foto',
                'Raccolta cartografie',
                'Descrizione stato di fatto',
                'Descrizione intervento',
                'Valutazione inserimento paesaggistico',
                'Redazione relazione',
                'Consegna elaborato',
            ],
            'checklist': [
                'Estratto mappa',
                'Ortofoto',
                'CTR',
                'Estratto vincoli',
                'Estratto PRG / PI',
                'Documentazione fotografica',
                'Coni visuali',
                'Elaborati progetto',
                'Relazione paesaggistica firmata',
            ],
        },
        {
            'nome': 'Sanatoria edilizia',
            'categoria': 'EDILIZIA',
            'descrizione': 'Pratica edilizia in sanatoria.',
            'fasi': [
                'Rilievo stato attuale',
                'Verifica stato legittimo',
                'Verifica conformità urbanistica',
                'Redazione elaborati comparativi',
                'Calcolo oblazioni e sanzioni',
                'Presentazione pratica',
                'Gestione istruttoria',
                'Rilascio provvedimento',
            ],
            'checklist': [
                'Documento committente',
                'Titolo di proprietà',
                'Documenti stato legittimo',
                'Elaborati stato autorizzato',
                'Elaborati stato attuale',
                'Relazione tecnica',
                'Calcolo sanzione',
                'Ricevute pagamento',
            ],
        },
        {
            'nome': 'Altro',
            'categoria': 'ALTRO',
            'descrizione': 'Workflow generico per pratiche non classificate.',
            'fasi': [
                'Apertura incarico',
                'Raccolta documenti',
                'Istruttoria tecnica',
                'Predisposizione elaborati',
                'Consegna o invio pratica',
                'Archiviazione',
            ],
            'checklist': [
                'Documento cliente',
                'Incarico professionale',
                'Documentazione ricevuta',
                'Elaborati prodotti',
                'Conferma consegna',
            ],
        },
    ]

    creati = []
    aggiornati = []

    for ordine_workflow, dati in enumerate(workflow_data, start=1):
        nome = dati['nome']

        workflow = TipoWorkflow.objects.filter(nome=nome).first()

        if workflow:
            aggiornati.append(nome)
        else:
            workflow = TipoWorkflow(nome=nome)
            creati.append(nome)

        workflow.categoria = dati['categoria']
        workflow.descrizione = dati['descrizione']
        workflow.attivo = True
        workflow.ordine = ordine_workflow
        workflow.save()

        # Pulisco fasi e checklist esistenti per evitare doppioni
        FaseWorkflow.objects.filter(workflow=workflow).delete()
        ChecklistWorkflow.objects.filter(workflow=workflow).delete()

        for ordine_fase, titolo_fase in enumerate(dati['fasi'], start=1):
            FaseWorkflow.objects.create(
                workflow=workflow,
                titolo=titolo_fase,
                descrizione='',
                ordine=ordine_fase,
                giorni_scadenza=None
            )

        for ordine_voce, voce in enumerate(dati['checklist'], start=1):
            ChecklistWorkflow.objects.create(
                workflow=workflow,
                voce=voce,
                descrizione='',
                obbligatorio=True,
                ordine=ordine_voce
            )

    testo = 'Caricamento workflow base completato.\n\n'

    testo += f'Workflow creati: {len(creati)}\n'
    for nome in creati:
        testo += f'- {nome}\n'

    testo += f'\nWorkflow aggiornati: {len(aggiornati)}\n'
    for nome in aggiornati:
        testo += f'- {nome}\n'

    testo += '\nFasi e checklist sono state rigenerate.\n'
    testo += 'Ora apri una pratica e controlla il workflow.'

    return HttpResponse(
        testo,
        content_type='text/plain'
    )