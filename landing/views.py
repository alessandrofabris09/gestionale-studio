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


def carica_workflow_professionali(request, codice):
    """
    Funzione temporanea.
    Carica o aggiorna i workflow professionali standard per studio tecnico.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'CARICA-WORKFLOW-PROFESSIONALI-2026'

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
            'descrizione': 'Richiesta di accesso agli atti edilizi, urbanistici o catastali presso enti pubblici.',
            'fasi': [
                'Apertura incarico',
                'Raccolta documento, delega e dati immobile',
                'Individuazione pratiche edilizie da richiedere',
                'Compilazione richiesta accesso atti',
                'Pagamento diritti di segreteria',
                'Invio richiesta all’ente competente',
                'Monitoraggio risposta dell’ente',
                'Ricezione e download documentazione',
                'Verifica completezza atti ricevuti',
                'Consegna documentazione al cliente',
                'Archiviazione pratica',
            ],
            'checklist': [
                'Documento identità richiedente',
                'Codice fiscale richiedente',
                'Delega accesso atti firmata',
                'Titolo di proprietà o incarico del proprietario',
                'Visura catastale',
                'Estratto mappa catastale',
                'Dati catastali completi',
                'Modulo accesso atti',
                'Ricevuta pagamento diritti',
                'Protocollo richiesta',
                'Documentazione ricevuta dall’ente',
            ],
        },
        {
            'nome': 'CILA',
            'categoria': 'EDILIZIA',
            'descrizione': 'Comunicazione Inizio Lavori Asseverata per manutenzione straordinaria e opere interne.',
            'fasi': [
                'Apertura incarico',
                'Sopralluogo e rilievo stato di fatto',
                'Verifica stato legittimo',
                'Verifica conformità urbanistica e catastale',
                'Redazione elaborati stato di fatto',
                'Redazione elaborati stato di progetto',
                'Redazione relazione tecnica asseverata',
                'Raccolta documenti impresa se presente',
                'Compilazione modulistica comunale',
                'Pagamento diritti di segreteria',
                'Invio CILA al Comune',
                'Archiviazione protocollo',
                'Eventuale comunicazione fine lavori',
            ],
            'checklist': [
                'Documento identità committente',
                'Codice fiscale committente',
                'Titolo di proprietà',
                'Visura catastale',
                'Planimetria catastale',
                'Estratto mappa',
                'Documentazione stato legittimo',
                'Elaborati stato di fatto',
                'Elaborati stato di progetto',
                'Relazione tecnica asseverata',
                'Modulo CILA',
                'Impresa esecutrice',
                'DURC impresa se dovuto',
                'Notifica preliminare se dovuta',
                'Ricevuta diritti di segreteria',
                'Ricevuta protocollo comunale',
            ],
        },
        {
            'nome': 'CILA in sanatoria',
            'categoria': 'EDILIZIA',
            'descrizione': 'Comunicazione in sanatoria per opere già eseguite e sanabili mediante CILA.',
            'fasi': [
                'Apertura incarico',
                'Rilievo dello stato attuale',
                'Ricostruzione stato legittimo',
                'Verifica opere difformi',
                'Verifica sanabilità dell’intervento',
                'Redazione elaborati comparativi',
                'Redazione relazione tecnica asseverata',
                'Calcolo sanzione',
                'Compilazione modulistica',
                'Invio pratica in sanatoria',
                'Archiviazione ricevute e protocollo',
            ],
            'checklist': [
                'Documento identità committente',
                'Codice fiscale committente',
                'Titolo di proprietà',
                'Visura catastale',
                'Planimetria catastale',
                'Titoli edilizi precedenti',
                'Elaborati stato legittimo',
                'Elaborati stato rilevato',
                'Elaborati comparativi',
                'Relazione tecnica asseverata',
                'Calcolo sanzione',
                'Ricevuta pagamento sanzione',
                'Ricevuta protocollo comunale',
            ],
        },
        {
            'nome': 'SCIA',
            'categoria': 'EDILIZIA',
            'descrizione': 'Segnalazione Certificata di Inizio Attività per interventi edilizi soggetti a SCIA.',
            'fasi': [
                'Apertura incarico',
                'Sopralluogo e rilievo',
                'Verifica stato legittimo',
                'Verifica normativa urbanistica',
                'Redazione progetto edilizio',
                'Redazione asseverazione tecnica',
                'Raccolta allegati impresa',
                'Verifica sicurezza cantiere',
                'Compilazione modulistica SCIA',
                'Invio pratica',
                'Gestione integrazioni',
                'Comunicazione fine lavori',
                'Archiviazione pratica',
            ],
            'checklist': [
                'Documento identità committente',
                'Titolo di proprietà',
                'Visura catastale',
                'Planimetria catastale',
                'Estratto mappa',
                'Titoli edilizi precedenti',
                'Elaborati grafici',
                'Relazione tecnica asseverata',
                'Modulo SCIA',
                'Dati impresa',
                'DURC impresa',
                'Notifica preliminare se dovuta',
                'Ricevuta diritti',
                'Protocollo SCIA',
                'Fine lavori',
            ],
        },
        {
            'nome': 'Permesso di Costruire',
            'categoria': 'EDILIZIA',
            'descrizione': 'Istanza di Permesso di Costruire per nuova costruzione, ampliamento o interventi rilevanti.',
            'fasi': [
                'Apertura incarico',
                'Verifica urbanistica preliminare',
                'Sopralluogo e rilievo',
                'Studio fattibilità progettuale',
                'Redazione progetto architettonico',
                'Calcolo superfici, volumi e parametri',
                'Verifica standard, distanze e parcheggi',
                'Redazione relazione tecnica illustrativa',
                'Raccolta pareri e nulla osta',
                'Compilazione istanza PDC',
                'Invio pratica al Comune',
                'Gestione istruttoria e integrazioni',
                'Rilascio titolo edilizio',
                'Comunicazione inizio lavori',
            ],
            'checklist': [
                'Documento identità committente',
                'Codice fiscale committente',
                'Titolo di proprietà',
                'Estratto mappa',
                'Visura catastale',
                'Planimetria catastale se presente',
                'Estratto PRG / PI',
                'Estratto vincoli',
                'Elaborati grafici completi',
                'Relazione tecnica illustrativa',
                'Calcolo superfici e volumi',
                'Verifica parcheggi',
                'Relazione energetica se dovuta',
                'Pareri enti competenti',
                'Ricevuta diritti di segreteria',
                'Ricevuta protocollo',
            ],
        },
        {
            'nome': 'Agibilità / SCA',
            'categoria': 'EDILIZIA',
            'descrizione': 'Segnalazione Certificata di Agibilità o documentazione finale di agibilità.',
            'fasi': [
                'Apertura incarico',
                'Verifica titolo edilizio e fine lavori',
                'Raccolta certificazioni impianti',
                'Raccolta collaudi e dichiarazioni',
                'Verifica accatastamento aggiornato',
                'Compilazione modulistica SCA',
                'Invio segnalazione',
                'Archiviazione ricevute',
            ],
            'checklist': [
                'Documento committente',
                'Titolo edilizio di riferimento',
                'Fine lavori',
                'Collaudo statico se dovuto',
                'Dichiarazioni conformità impianti',
                'APE se dovuto',
                'DOCFA aggiornato',
                'Planimetria catastale aggiornata',
                'Dichiarazione salubrità',
                'Modulo SCA',
                'Ricevuta protocollo',
            ],
        },
        {
            'nome': 'Autorizzazione paesaggistica semplificata',
            'categoria': 'AMBIENTE',
            'descrizione': 'Autorizzazione paesaggistica con procedimento semplificato.',
            'fasi': [
                'Verifica vincolo paesaggistico',
                'Verifica assoggettabilità a procedura semplificata',
                'Sopralluogo e foto',
                'Raccolta estratti cartografici',
                'Redazione elaborati di progetto',
                'Redazione relazione paesaggistica semplificata',
                'Invio istanza',
                'Gestione eventuali integrazioni',
                'Ricezione autorizzazione',
            ],
            'checklist': [
                'Documento richiedente',
                'Titolo di proprietà',
                'Estratto mappa',
                'Ortofoto',
                'CTR',
                'Estratto PRG / PI',
                'Estratto vincoli',
                'Documentazione fotografica',
                'Coni visuali',
                'Elaborati stato di fatto',
                'Elaborati stato di progetto',
                'Relazione paesaggistica semplificata',
                'Ricevuta diritti',
            ],
        },
        {
            'nome': 'Autorizzazione paesaggistica ordinaria',
            'categoria': 'AMBIENTE',
            'descrizione': 'Autorizzazione paesaggistica ordinaria per interventi in area vincolata.',
            'fasi': [
                'Analisi vincoli e contesto paesaggistico',
                'Sopralluogo e rilievo fotografico',
                'Raccolta cartografie e strumenti urbanistici',
                'Descrizione stato dei luoghi',
                'Descrizione intervento di progetto',
                'Valutazione compatibilità paesaggistica',
                'Redazione relazione paesaggistica ordinaria',
                'Predisposizione elaborati grafici',
                'Invio istanza',
                'Gestione istruttoria Comune/Soprintendenza',
                'Ricezione provvedimento',
            ],
            'checklist': [
                'Documento richiedente',
                'Titolo di proprietà',
                'Estratto mappa catastale',
                'Ortofoto',
                'CTR',
                'Estratto carta dei vincoli',
                'Estratto PRG / PI',
                'Documentazione fotografica',
                'Coni visuali fotografici',
                'Elaborati stato di fatto',
                'Elaborati stato di progetto',
                'Relazione paesaggistica ordinaria',
                'Fotoinserimento o render se necessario',
                'Ricevuta diritti',
                'Parere Soprintendenza se acquisito',
            ],
        },
        {
            'nome': 'Compatibilità paesaggistica',
            'categoria': 'AMBIENTE',
            'descrizione': 'Accertamento di compatibilità paesaggistica per opere già realizzate.',
            'fasi': [
                'Verifica opere eseguite',
                'Verifica vincolo paesaggistico',
                'Verifica ammissibilità accertamento',
                'Sopralluogo e documentazione fotografica',
                'Redazione elaborati comparativi',
                'Redazione relazione di compatibilità',
                'Presentazione istanza',
                'Gestione istruttoria',
                'Rilascio provvedimento',
            ],
            'checklist': [
                'Documento richiedente',
                'Titolo di proprietà',
                'Estratto mappa',
                'Estratto vincoli',
                'Documentazione fotografica',
                'Elaborati stato autorizzato',
                'Elaborati stato rilevato',
                'Elaborati comparativi',
                'Relazione di compatibilità paesaggistica',
                'Ricevuta diritti',
                'Provvedimento finale',
            ],
        },
        {
            'nome': 'DOCFA - Variazione',
            'categoria': 'CATASTO',
            'descrizione': 'Variazione catastale DOCFA per unità immobiliari esistenti.',
            'fasi': [
                'Raccolta documentazione catastale',
                'Sopralluogo e rilievo immobile',
                'Verifica intestazione catastale',
                'Predisposizione planimetria catastale',
                'Compilazione DOCFA',
                'Verifica classamento e rendita',
                'Invio telematico',
                'Verifica ricevuta approvazione',
                'Consegna documentazione al cliente',
            ],
            'checklist': [
                'Documento intestatario',
                'Codice fiscale intestatario',
                'Titolo di proprietà',
                'Visura catastale',
                'Planimetria catastale precedente',
                'Elaborato planimetrico se presente',
                'Rilievo aggiornato',
                'Planimetria catastale nuova',
                'File DOCFA',
                'Ricevuta invio',
                'Ricevuta approvazione',
                'Visura aggiornata',
            ],
        },
        {
            'nome': 'DOCFA - Nuova costruzione',
            'categoria': 'CATASTO',
            'descrizione': 'Accatastamento nuova costruzione o nuove unità immobiliari urbane.',
            'fasi': [
                'Raccolta titolo edilizio e dati catastali',
                'Rilievo fabbricato',
                'Predisposizione elaborato planimetrico',
                'Predisposizione planimetrie unità',
                'Compilazione DOCFA nuova costruzione',
                'Verifica classamento',
                'Invio telematico',
                'Controllo ricevute',
                'Consegna elaborati',
            ],
            'checklist': [
                'Documento intestatario',
                'Titolo di proprietà',
                'Titolo edilizio',
                'Tipo mappale approvato',
                'Estratto mappa aggiornato',
                'Elaborato planimetrico',
                'Planimetrie catastali',
                'File DOCFA',
                'Ricevuta invio',
                'Ricevuta approvazione',
                'Visura aggiornata',
            ],
        },
        {
            'nome': 'PREGEO - Frazionamento',
            'categoria': 'CATASTO',
            'descrizione': 'Tipo di frazionamento catastale mediante PREGEO.',
            'fasi': [
                'Raccolta documentazione catastale',
                'Verifica intestazioni e mappa',
                'Sopralluogo e rilievo topografico',
                'Definizione nuove dividenti',
                'Elaborazione libretto misure',
                'Predisposizione proposta aggiornamento',
                'Compilazione PREGEO',
                'Invio telematico',
                'Verifica approvazione',
                'Consegna elaborati al cliente',
            ],
            'checklist': [
                'Documento intestatari',
                'Titolo di proprietà',
                'Visure catastali',
                'Estratto mappa',
                'Monografie punti fiduciali',
                'Libretto misure',
                'Schema frazionamento',
                'Proposta aggiornamento',
                'Relazione tecnica',
                'File PREGEO',
                'Ricevuta invio',
                'Approvazione Agenzia Entrate',
            ],
        },
        {
            'nome': 'PREGEO - Tipo mappale',
            'categoria': 'CATASTO',
            'descrizione': 'Tipo mappale per inserimento o aggiornamento fabbricato in mappa.',
            'fasi': [
                'Raccolta documentazione catastale',
                'Verifica mappa e intestazioni',
                'Rilievo topografico fabbricato',
                'Elaborazione libretto misure',
                'Predisposizione proposta tipo mappale',
                'Compilazione PREGEO',
                'Invio telematico',
                'Verifica approvazione',
                'Passaggio a DOCFA se necessario',
            ],
            'checklist': [
                'Documento intestatari',
                'Titolo di proprietà',
                'Visure catastali',
                'Estratto mappa',
                'Monografie punti fiduciali',
                'Libretto misure',
                'Sagoma fabbricato',
                'Proposta aggiornamento',
                'File PREGEO',
                'Ricevuta invio',
                'Approvazione tipo mappale',
            ],
        },
        {
            'nome': 'APE',
            'categoria': 'ENERGIA',
            'descrizione': 'Attestato di Prestazione Energetica.',
            'fasi': [
                'Apertura incarico',
                'Raccolta dati catastali',
                'Sopralluogo obbligatorio',
                'Rilievo involucro edilizio',
                'Raccolta dati impianti',
                'Elaborazione software energetico',
                'Redazione APE',
                'Deposito al catasto energetico regionale',
                'Consegna attestato al cliente',
            ],
            'checklist': [
                'Documento proprietario',
                'Codice fiscale proprietario',
                'Visura catastale',
                'Planimetria catastale',
                'Libretto impianto',
                'Dati generatore',
                'Dati serramenti',
                'Dati isolamento se disponibili',
                'Foto immobile',
                'File APE firmato',
                'Ricevuta deposito regionale',
            ],
        },
        {
            'nome': 'ENEA Bonus Casa',
            'categoria': 'ENERGIA',
            'descrizione': 'Comunicazione ENEA per interventi Bonus Casa con risparmio energetico.',
            'fasi': [
                'Raccolta dati committente',
                'Raccolta dati catastali immobile',
                'Verifica data fine lavori',
                'Raccolta fatture e bonifici',
                'Raccolta schede tecniche prodotti',
                'Verifica interventi da comunicare',
                'Compilazione portale ENEA',
                'Invio comunicazione',
                'Consegna ricevuta CPID',
            ],
            'checklist': [
                'Documento committente',
                'Codice fiscale committente',
                'Dati catastali immobile',
                'Data fine lavori',
                'Fatture interventi',
                'Bonifici parlanti',
                'Schede tecniche prodotti',
                'Dati serramenti se presenti',
                'Dati caldaia o impianto se presenti',
                'Dichiarazione installatore se disponibile',
                'Ricevuta ENEA / CPID',
            ],
        },
        {
            'nome': 'ENEA Ecobonus',
            'categoria': 'ENERGIA',
            'descrizione': 'Comunicazione ENEA per interventi Ecobonus.',
            'fasi': [
                'Raccolta dati committente',
                'Verifica intervento agevolabile',
                'Raccolta schede tecniche e asseverazioni',
                'Raccolta fatture e bonifici',
                'Verifica requisiti energetici',
                'Compilazione portale ENEA Ecobonus',
                'Invio comunicazione',
                'Consegna ricevuta CPID',
            ],
            'checklist': [
                'Documento committente',
                'Codice fiscale committente',
                'Dati catastali immobile',
                'Data fine lavori',
                'Fatture',
                'Bonifici parlanti',
                'Schede tecniche',
                'Asseverazione se dovuta',
                'Dichiarazione congruità se dovuta',
                'Dati prestazionali ante e post intervento',
                'Ricevuta ENEA / CPID',
            ],
        },
        {
            'nome': 'Perizia estimativa',
            'categoria': 'ALTRO',
            'descrizione': 'Perizia estimativa o valutazione tecnica di immobile, area o danno.',
            'fasi': [
                'Apertura incarico',
                'Raccolta documentazione',
                'Sopralluogo',
                'Analisi urbanistica e catastale',
                'Analisi comparativa valori',
                'Redazione perizia',
                'Revisione finale',
                'Consegna al cliente',
            ],
            'checklist': [
                'Incarico professionale',
                'Documento cliente',
                'Titolo di proprietà',
                'Visura catastale',
                'Estratto mappa',
                'Planimetria catastale',
                'Documentazione fotografica',
                'Valori OMI o comparabili',
                'Elaborati grafici se necessari',
                'Perizia firmata',
            ],
        },
        {
            'nome': 'Relazione tecnica illustrativa',
            'categoria': 'ALTRO',
            'descrizione': 'Relazione tecnica descrittiva o illustrativa da allegare a pratiche edilizie o istanze.',
            'fasi': [
                'Raccolta dati intervento',
                'Sopralluogo',
                'Verifica documentazione',
                'Analisi normativa',
                'Redazione relazione',
                'Controllo coerenza con elaborati',
                'Consegna o allegazione alla pratica',
            ],
            'checklist': [
                'Dati committente',
                'Dati immobile',
                'Estratto mappa',
                'Visura catastale',
                'Documentazione fotografica',
                'Elaborati grafici',
                'Normativa di riferimento',
                'Relazione tecnica firmata',
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

        workflow = TipoWorkflow.objects.filter(
            nome=dati['nome']
        ).first()

        if workflow:
            aggiornati.append(dati['nome'])
        else:
            workflow = TipoWorkflow(
                nome=dati['nome']
            )
            creati.append(dati['nome'])

        workflow.categoria = dati['categoria']
        workflow.descrizione = dati['descrizione']
        workflow.attivo = True
        workflow.ordine = ordine_workflow
        workflow.save()

        FaseWorkflow.objects.filter(
            workflow=workflow
        ).delete()

        ChecklistWorkflow.objects.filter(
            workflow=workflow
        ).delete()

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

    testo = 'Caricamento workflow professionali completato.\n\n'

    testo += f'Workflow creati: {len(creati)}\n'
    for nome in creati:
        testo += f'- {nome}\n'

    testo += f'\nWorkflow aggiornati: {len(aggiornati)}\n'
    for nome in aggiornati:
        testo += f'- {nome}\n'

    testo += '\nFasi e checklist sono state rigenerate.\n'
    testo += 'Ora controlla la tendina tipo pratica e il workflow delle pratiche.\n'

    return HttpResponse(
        testo,
        content_type='text/plain'
    )


def pulisci_workflow_doppi(request, codice):
    """
    Funzione temporanea.
    Disattiva i vecchi workflow generici caricati prima dei workflow professionali.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'PULISCI-WORKFLOW-DOPPI-2026'

    if codice != CODICE_SICUREZZA:
        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    workflow_da_disattivare = [
        'Autorizzazione Paesaggistica',
        'Compatibilità Paesaggistica',
        'DOCFA',
        'PREGEO',
        'Frazionamento',
        'Tipo mappale',
        'Voltura catastale',
        'Successione',
        'Perizia tecnica',
        'Relazione tecnica',
        'Relazione paesaggistica',
        'Sanatoria edilizia',
        'ENEA',
        'Pratica catastale',
        'Computo metrico',
        'Direzione lavori',
        'Sicurezza cantiere',
        'Comunicazione fine lavori',
        'Accertamento di conformità',
    ]

    disattivati = []
    non_trovati = []

    for nome in workflow_da_disattivare:
        workflow = TipoWorkflow.objects.filter(nome=nome).first()

        if workflow:
            workflow.attivo = False
            workflow.save()
            disattivati.append(nome)
        else:
            non_trovati.append(nome)

    testo = 'Pulizia workflow doppi completata.\n\n'

    testo += f'Workflow disattivati: {len(disattivati)}\n'
    for nome in disattivati:
        testo += f'- {nome}\n'

    testo += f'\nWorkflow non trovati: {len(non_trovati)}\n'
    for nome in non_trovati:
        testo += f'- {nome}\n'

    testo += '\nOra controlla la tendina Tipo pratica.\n'

    return HttpResponse(
        testo,
        content_type='text/plain'
    )    