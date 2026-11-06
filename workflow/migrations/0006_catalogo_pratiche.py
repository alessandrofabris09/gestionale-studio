from django.db import migrations


# I passaggi sono promemoria di lavoro. Modulistica e allegati si verificano
# presso lo sportello competente per l'intervento.
CATALOGO = {
    'EDILIZIA': (
        'Inquadramento e accesso agli atti|Rilievo e verifica dello stato legittimo|Elaborati e verifiche|Presentazione e protocollo|Gestione esito',
        'CILA|CILA tardiva|SCIA edilizia|SCIA alternativa al permesso di costruire|Permesso di costruire|'
        'Permesso di costruire convenzionato|Permesso di costruire in deroga|'
        'SCIA in sanatoria|Permesso di costruire in sanatoria|Condono edilizio - definizione istanza|'
        'CIL per opere temporanee|Edilizia libera - verifica tecnica|Cambio di destinazione d’uso|'
        'Variante in corso d’opera|Proroga del titolo edilizio|Voltura del titolo edilizio|'
        'Comunicazione inizio lavori|Comunicazione fine lavori|SCIA per l’agibilità (SCA)|'
        'Agibilità parziale|Tolleranze costruttive ed esecutive|Recupero sottotetto|'
        'Demolizione e ricostruzione|Installazione ascensore e abbattimento barriere architettoniche|'
        'Occupazione suolo pubblico per cantiere|Manomissione suolo pubblico|'
        'Autorizzazione passo carrabile|Richiesta attribuzione numero civico|Idoneità alloggiativa',
    ),
    'SUAP': (
        'Inquadramento attività e sportello|Verifica locali e procedimenti collegati|Preparazione moduli e allegati|Trasmissione e protocollo|Gestione esito',
        'SUAP - procedimento unico per impianto produttivo|SUAP - variante urbanistica per impianto produttivo|'
        'SUAP - SCIA unica|SUAP - SCIA condizionata|SUAP - collaudo impianto produttivo|'
        'SUAP - esercizio di vicinato|SUAP - media struttura di vendita|SUAP - grande struttura di vendita|'
        'SUAP - commercio su aree pubbliche|SUAP - commercio elettronico|SUAP - commercio all’ingrosso|'
        'SUAP - somministrazione di alimenti e bevande|SUAP - somministrazione temporanea|'
        'SUAP - notifica sanitaria alimentare|SUAP - panificazione|SUAP - attività artigianale|'
        'SUAP - acconciatore ed estetista|SUAP - autoriparazione|SUAP - distributore di carburante|'
        'SUAP - struttura ricettiva alberghiera|SUAP - struttura ricettiva extralberghiera|'
        'SUAP - agriturismo|SUAP - locazione turistica|SUAP - pubblico spettacolo e trattenimento|'
        'SUAP - agibilità locale di pubblico spettacolo|SUAP - insegne e mezzi pubblicitari|'
        'SUAP - impianti di telecomunicazione|SUAP - subingresso|SUAP - trasferimento sede|'
        'SUAP - ampliamento o modifica attività|SUAP - sospensione o riattivazione|SUAP - cessazione attività',
    ),
    'URBANISTICA': (
        'Inquadramento territoriale|Verifica vincoli e strumenti urbanistici|Relazione ed elaborati|Istanza e protocollo|Gestione esito',
        'Certificato di destinazione urbanistica (CDU)|Autorizzazione paesaggistica ordinaria|'
        'Autorizzazione paesaggistica semplificata|Accertamento di compatibilità paesaggistica|'
        'Intervento su bene culturale - autorizzazione|Piano attuativo|Piano di lottizzazione|'
        'Convenzione urbanistica|Variante urbanistica|Autorizzazione per vincolo idrogeologico|'
        'Parere preventivo urbanistico o edilizio',
    ),
    'CATASTO': (
        'Visure e documenti di riferimento|Verifiche e rilievo|Predisposizione della pratica catastale|Presentazione o richiesta|Verifica esito e dati aggiornati',
        'DOCFA - nuova costruzione|DOCFA - unità afferente|DOCFA - divisione|DOCFA - fusione|'
        'DOCFA - frazionamento e fusione|DOCFA - ampliamento|DOCFA - demolizione totale|'
        'DOCFA - demolizione parziale|DOCFA - diversa distribuzione degli spazi interni|'
        'DOCFA - ristrutturazione|DOCFA - cambio di destinazione d’uso|DOCFA - ultimazione fabbricato urbano|'
        'DOCFA - variazione toponomastica|DOCFA - esatta rappresentazione grafica|'
        'DOCFA - planimetria mancante|DOCFA - modifica identificativo|DOCFA - ruralità|'
        'DOCFA - rideterminazione rendita|DOCFA - beni comuni censibili e non censibili|'
        'PREGEO - tipo mappale|PREGEO - tipo di frazionamento|PREGEO - tipo mappale e frazionamento|'
        'PREGEO - tipo particellare|PREGEO - demolizione e aggiornamento mappa|'
        'PREGEO - fusione di particelle|PREGEO - conferma di mappa|'
        'Voltura catastale - afflusso|Voltura catastale - preallineamento|'
        'Voltura catastale - recupero voltura automatica|Voltura catastale - annotamento|'
        'Riunione di usufrutto|Rettifica dati catastali|Variazione colturale catasto terreni|'
        'Visura catastale attuale o storica|Richiesta planimetria catastale|'
        'Richiesta estratto di mappa|Elaborato planimetrico ed elenco subalterni|'
        'Richiesta monografia punto fiduciale|Istanza di aggiornamento punto fiduciale|'
        'Ispezione ipotecaria|Catasto tavolare - verifica e istanza locale',
    ),
    'SUCCESSIONI': (
        'Dati del defunto ed eredi|Verifica titoli e patrimonio|Compilazione e controllo|Invio e ricevute|Verifica delle volture',
        'Successione|Successione - dichiarazione sostitutiva|Successione - dichiarazione integrativa (modello 4)|'
        'Successione - dichiarazione modificativa (modello 4)|Successione - attestazione di presentazione|'
        'Successione - voltura catastale separata|Successione - inventario immobiliare',
    ),
    'STIME': (
        'Mandato e finalità della stima|Sopralluogo e raccolta dati|Analisi comparabili e criteri|Relazione di stima|Consegna',
        'Perizia di stima|Stima immobiliare di mercato|Stima di terreni agricoli|Stima di aree edificabili|'
        'Stima del canone di locazione|Stima per mutuo|Stima per divisione ereditaria|'
        'Stima danni immobiliari|Stima indennità di esproprio|Perizia asseverata o giurata|'
        'Consulenza tecnica d’ufficio (CTU)|Consulenza tecnica di parte (CTP)|Stima di usufrutto e nuda proprietà',
    ),
    'ENERGIA': (
        'Raccolta dati edificio e impianti|Rilievo o verifica documentale|Calcolo e redazione|Consegna o trasmissione|Archiviazione esito',
        'APE - Attestato di prestazione energetica|APE - aggiornamento attestato|AQE - Attestato di qualificazione energetica|'
        'ENEA - Ecobonus|ENEA - Bonus Casa|ENEA - Superbonus e asseverazioni|'
        'Relazione tecnica energetica (Legge 10)|Diagnosi energetica|'
        'Verifica requisiti minimi energetici|Conto Termico - pratica GSE|Impianto fotovoltaico - connessione e pratiche GSE',
    ),
    'STRUTTURE': (
        'Raccolta dati e rilievo|Inquadramento strutturale e sismico|Progetto e verifiche|Deposito o autorizzazione|Esito e archiviazione',
        'Deposito progetto strutturale|Autorizzazione sismica|Denuncia opere strutturali|'
        'Variante strutturale|Intervento locale su struttura esistente|Miglioramento sismico|'
        'Adeguamento sismico|Valutazione della sicurezza strutturale|Relazione a strutture ultimate|'
        'Collaudo statico|Dichiarazione di regolare esecuzione strutturale|Certificato di idoneità statica|'
        'Relazione geotecnica|Piano delle indagini geotecniche',
    ),
    'AMBIENTE': (
        'Inquadramento intervento e autorità|Verifica ambientale e documenti|Elaborati tecnici|Presentazione|Gestione prescrizioni',
        'AUA - Autorizzazione unica ambientale|AIA - Autorizzazione integrata ambientale|'
        'VIA - Valutazione di impatto ambientale|Verifica di assoggettabilità a VIA|VAS - Valutazione ambientale strategica|'
        'VIncA - Valutazione di incidenza|Autorizzazione allo scarico|Allacciamento alla fognatura|'
        'Autorizzazione emissioni in atmosfera|Gestione terre e rocce da scavo|Piano di caratterizzazione e bonifica|'
        'Autorizzazione impianto rifiuti|Concessione di derivazione acqua|Autorizzazione idraulica|'
        'Compatibilità idraulica e invarianza idraulica|Piano di lavoro rimozione amianto',
    ),
    'ANTINCENDIO': (
        'Inquadramento attività|Rilievo e valutazione|Progetto o asseverazione|Presentazione ai Vigili del Fuoco|Gestione esito',
        'Valutazione progetto antincendio|SCIA antincendio|Rinnovo periodico conformità antincendio|'
        'Deroga antincendio|Nulla osta di fattibilità antincendio|Verifica in corso d’opera antincendio',
    ),
    'ACUSTICA': (
        'Raccolta dati e classificazione|Rilievi e misure|Valutazione e relazione|Consegna o deposito',
        'Valutazione previsionale di impatto acustico|Valutazione previsionale di clima acustico|'
        'Requisiti acustici passivi|Collaudo acustico|Autorizzazione in deroga per attività rumorosa',
    ),
    'IMPIANTI': (
        'Rilievo ed esigenze|Dimensionamento e progetto|Verifica e coordinamento|Consegna e documentazione finale',
        'Progetto impianto elettrico|Progetto impianto termico|Progetto impianto gas|'
        'Progetto impianto idrico sanitario|Progetto ventilazione e climatizzazione|'
        'Dichiarazione di conformità impianto - raccolta e verifica|Dichiarazione di rispondenza impianto|'
        'Collaudo e verifica funzionale impianti|Impianto di sollevamento - messa in esercizio',
    ),
    'RILIEVI': (
        'Definizione incarico e riferimenti|Rilievo sul campo|Elaborazione e controllo|Consegna',
        'Rilievo architettonico|Rilievo topografico GNSS o stazione totale|Rilievo laser scanner|'
        'Rilievo fotogrammetrico o con drone|Riconfinamento|Tracciamento di cantiere|'
        'Rilievo dello stato di fatto e restituzione BIM',
    ),
    'SICUREZZA_CANTIERI': (
        'Inquadramento incarico|Verifica documentazione e rischi|Predisposizione atti|Monitoraggio e aggiornamenti|Chiusura',
        'Coordinamento sicurezza in progettazione (CSP)|Coordinamento sicurezza in esecuzione (CSE)|'
        'Piano di sicurezza e coordinamento (PSC)|Piano operativo di sicurezza (POS)|'
        'Notifica preliminare cantiere|Fascicolo dell’opera|PiMUS ponteggi|Verifica idoneità tecnico professionale',
    ),
    'LAVORI_PUBBLICI': (
        'Inquadramento incarico e dati|Sviluppo elaborati|Verifiche e consegna|Gestione esito',
        'Progetto di fattibilità tecnico-economica (PFTE)|Progetto esecutivo|Direzione lavori|'
        'Computo metrico estimativo|Capitolato speciale d’appalto|Contabilità lavori e SAL|'
        'Perizia di variante lavori|Certificato di regolare esecuzione|Collaudo tecnico amministrativo',
    ),
    'PRATICHE_IMMOBILIARI_NOTARILI': (
        'Raccolta documenti|Verifiche urbanistiche e catastali|Relazione e coordinamento|Consegna',
        'Accesso atti|Relazione tecnica integrata|Compravendita|Divisione|Donazione|'
        'Due diligence immobiliare|Tabelle millesimali|Verifica conformità urbanistica e catastale|'
        'Relazione sullo stato legittimo',
    ),
}


MODELLI_DETTAGLIATI = {
    'CILA': (
        'Verifica dell’intervento e dello stato legittimo|Rilievo ed elaborati comparativi|'
        'Asseverazione e allegati|Deposito e ricevuta|Chiusura e verifiche finali',
        'Delega e dati dei soggetti|Titoli edilizi di riferimento|Elaborati ante e post operam|Ricevuta del deposito',
    ),
    'DOCFA - nuova costruzione': (
        'Verifica atti del Catasto terreni|Rilievo e individuazione delle unità|'
        'Planimetrie ed elaborato planimetrico|Classamento e compilazione DOCFA|Invio e verifica registrazione',
        'Estremi del tipo mappale|Planimetrie delle unità|Elaborato planimetrico ed elenco subalterni se pertinenti|Ricevuta catastale',
    ),
    'PREGEO - tipo di frazionamento': (
        'Acquisizione estratto di mappa|Ricognizione dei punti di appoggio e rilievo|'
        'Elaborazione libretto e proposta di aggiornamento|Verifica deposito e invio|Controllo mappa e identificativi',
        'Estratto di mappa|Libretto delle misure|Proposta di aggiornamento|Ricevuta di approvazione',
    ),
    'Successione': (
        'Raccolta dati del defunto e degli eredi|Ricostruzione di titoli, quote e patrimonio|'
        'Compilazione dichiarazione e volture|Invio telematico e verifica ricevute|Verifica intestazioni aggiornate',
        'Dati anagrafici e fiscali degli interessati|Documentazione sui titoli e sugli immobili|'
        'Testamento o altra documentazione se pertinente|Attestazione di presentazione',
    ),
    'APE - Attestato di prestazione energetica': (
        'Acquisizione dati dell’immobile e degli impianti|Sopralluogo e rilievo energetico|'
        'Calcolo della prestazione e redazione APE|Trasmissione al sistema competente|Consegna e archiviazione',
        'Identificativi catastali|Documentazione degli impianti se disponibile|Rilievo involucro e impianti|Attestato e ricevuta',
    ),
    'ENEA - Bonus Casa': (
        'Verifica intervento e periodo di riferimento|Raccolta dati tecnici e fine lavori|'
        'Compilazione scheda Bonus Casa|Trasmissione e ricevuta|Consegna al committente',
        'Dati del beneficiario e dell’immobile|Dati tecnici dell’intervento|Data di fine lavori|Ricevuta ENEA',
    ),
    'ENEA - Ecobonus': (
        'Verifica intervento e portale di riferimento|Raccolta dati prima e dopo l’intervento|'
        'Predisposizione documenti e scheda Ecobonus|Trasmissione e ricevuta|Consegna al committente',
        'Schede tecniche dei componenti|Dati delle prestazioni energetiche|Asseverazione o documenti previsti per il caso|Ricevuta ENEA',
    ),
}


def popola_catalogo(apps, schema_editor):
    modelli = apps.get_model('workflow', 'TipoWorkflow').objects.using(schema_editor.connection.alias)
    fasi = apps.get_model('workflow', 'FaseWorkflow').objects.using(schema_editor.connection.alias)
    checklist = apps.get_model('workflow', 'ChecklistWorkflow').objects.using(schema_editor.connection.alias)
    for categoria, (passaggi, nomi) in CATALOGO.items():
        for nome in nomi.split('|'):
            esistente = modelli.filter(studio__isnull=True, nome=nome).order_by('pk').first()
            if esistente:
                if nome in {'Successione', 'Perizia di stima'}:
                    modelli.filter(pk=esistente.pk, categoria='PRATICHE_IMMOBILIARI_NOTARILI').update(
                        categoria=categoria,
                    )
                continue
            modello = modelli.create(studio=None, nome=nome, categoria=categoria, attivo=True)
            passaggi_modello, voci = MODELLI_DETTAGLIATI.get(nome, (passaggi, ''))
            fasi.bulk_create([
                fasi.model(workflow_id=modello.pk, titolo=titolo, ordine=ordine)
                for ordine, titolo in enumerate(passaggi_modello.split('|'), start=1)
            ])
            if voci:
                checklist.bulk_create([
                    checklist.model(workflow_id=modello.pk, voce=voce, ordine=ordine, obbligatorio=False)
                    for ordine, voce in enumerate(voci.split('|'), start=1)
                ])


class Migration(migrations.Migration):
    dependencies = [('workflow', '0005_alter_tipoworkflow_categoria')]
    operations = [migrations.RunPython(popola_catalogo, migrations.RunPython.noop)]
