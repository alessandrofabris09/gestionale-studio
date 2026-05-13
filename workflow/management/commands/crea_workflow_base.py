from django.core.management.base import BaseCommand

from workflow.models import (
    TipoWorkflow,
    FaseWorkflow,
    ChecklistWorkflow,
)


WORKFLOW_BASE = [

    {
        'categoria': 'EDILIZIA',
        'nome': 'CILA',

        'fasi': [
            'Raccolta documentazione',
            'Rilievo',
            'Verifica conformità urbanistica-edilizia',
            'Redazione elaborati grafici',
            'Relazione tecnica asseverata',
            'Compilazione pratica edilizia',
            'Deposito pratica',
            'Fine lavori',
        ],

        'checklist': [
            'Documento identità',
            'Codice fiscale',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'Estratto mappa',
            'Documentazione fotografica',
            'Relazione tecnica',
            'Elaborati grafici',
            'Ricevuta diritti',
            'Impresa esecutrice',
            'DURC impresa',
        ]
    },

    {
        'categoria': 'EDILIZIA',
        'nome': 'SCIA',

        'fasi': [
            'Raccolta documentazione',
            'Rilievo',
            'Verifica conformità urbanistica-edilizia',
            'Redazione elaborati grafici',
            'Relazione tecnica asseverata',
            'Compilazione pratica edilizia',
            'Deposito SCIA',
            'Monitoraggio istruttoria',
            'Fine lavori',
        ],

        'checklist': [
            'Documento identità',
            'Codice fiscale',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'Estratto mappa',
            'Documentazione fotografica',
            'Relazione tecnica',
            'Elaborati grafici',
            'Ricevuta diritti',
            'Impresa esecutrice',
            'DURC impresa',
        ]
    },

    {
        'categoria': 'EDILIZIA',
        'nome': 'Permesso di Costruire',

        'fasi': [
            'Raccolta documentazione',
            'Rilievo',
            'Verifica urbanistica',
            'Predisposizione progetto',
            'Compilazione pratica edilizia',
            'Deposito pratica',
            'Monitoraggio istruttoria',
            'Rilascio permesso',
            'Fine lavori',
        ],

        'checklist': [
            'Documento identità',
            'Codice fiscale',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'Estratto mappa',
            'Documentazione fotografica',
            'Relazione tecnica',
            'Elaborati grafici',
            'Computo metrico',
            'Ricevuta diritti',
        ]
    },

    {
        'categoria': 'EDILIZIA',
        'nome': 'Sanatoria',

        'fasi': [
            'Raccolta documentazione',
            'Verifica sanabilità',
            'Rilievo abuso',
            'Ricostruzione stato legittimo',
            'Relazione sanatoria',
            'Deposito istanza',
            'Monitoraggio istruttoria',
            'Rilascio sanatoria',
            'DOCFA post-sanatoria',
        ],

        'checklist': [
            'Documento identità',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'Documentazione fotografica',
            'Relazione sanabilità',
            'Elaborati comparativi',
            'Calcolo oblazione',
        ]
    },

    {
        'categoria': 'EDILIZIA',
        'nome': 'Agibilità',

        'fasi': [
            'Raccolta documentazione',
            'Verifica requisiti igienico-sanitari',
            'Verifica impianti',
            'Verifica accatastamento',
            'Predisposizione SCA',
            'Deposito pratica',
            'Archiviazione ricevuta',
        ],

        'checklist': [
            'Collaudo statico',
            'Dichiarazioni conformità impianti',
            'APE',
            'Accatastamento',
            'Fine lavori',
            'Documentazione fotografica',
        ]
    },

    {
        'categoria': 'EDILIZIA',
        'nome': 'Autorizzazione paesaggistica',

        'fasi': [
            'Verifica vincolo',
            'Raccolta documentazione',
            'Relazione paesaggistica',
            'Elaborati grafici',
            'Deposito pratica',
            'Monitoraggio istruttoria',
            'Rilascio autorizzazione',
        ],

        'checklist': [
            'Estratto vincoli',
            'Relazione paesaggistica',
            'Elaborati grafici',
            'Documentazione fotografica',
            'Titolo proprietà',
        ]
    },

    {
        'categoria': 'AMBIENTE',
        'nome': 'VINCA',

        'fasi': [
            'Verifica area SIC/ZPS',
            'Screening VINCA',
            'Relazione ambientale',
            'Cartografia',
            'Deposito pratica',
            'Monitoraggio istruttoria',
        ],

        'checklist': [
            'Relazione VINCA',
            'Cartografia',
            'Estratti SIC/ZPS',
            'Documentazione fotografica',
            'Descrizione intervento',
        ]
    },

    {
        'categoria': 'AMBIENTE',
        'nome': 'Autorizzazione scarico',

        'fasi': [
            'Rilievo impianto',
            'Verifica recapito scarico',
            'Relazione tecnica',
            'Compilazione domanda',
            'Deposito pratica',
            'Rilascio autorizzazione',
        ],

        'checklist': [
            'Relazione tecnica',
            'Schema impianto',
            'Documentazione fotografica',
            'Titolo proprietà',
            'Planimetria rete scarichi',
        ]
    },

    {
        'categoria': 'CATASTO',
        'nome': 'DOCFA',

        'fasi': [
            'Raccolta documentazione',
            'Rilievo',
            'Elaborazione planimetrie',
            'Compilazione DOCFA',
            'Invio Sister',
            'Ricevuta catastale',
        ],

        'checklist': [
            'Visura catastale',
            'Planimetria',
            'Estratto mappa',
            'Documento proprietà',
            'Delega',
            'Elaborato planimetrico',
        ]
    },

        {
        'categoria': 'CATASTO',
        'nome': 'PREGEO',

        'fasi': [
            'Rilievo GPS',
            'Verifica PF',
            'Compilazione libretto',
            'Proposta aggiornamento',
            'Invio PREGEO',
            'Ricevuta catastale',
        ],

        'checklist': [
            'Estratto di mappa',
            'Rilievo GPS',
            'Libretto PREGEO',
            'Documento proprietà',
            'Monografie PF',
        ]
    },

    {
        'categoria': 'CATASTO',
        'nome': 'DOCTE',

        'fasi': [
            'Raccolta documentazione',
            'Compilazione DOCTE',
            'Invio pratica',
            'Ricevuta',
        ],

        'checklist': [
            'Documento identità',
            'Visura catastale',
            'Titolo proprietà',
        ]
    },

    {
        'categoria': 'ENERGIA',
        'nome': 'APE',

        'fasi': [
            'Sopralluogo',
            'Raccolta dati impianti',
            'Elaborazione APE',
            'Invio portale regionale',
            'Consegna attestato',
        ],

        'checklist': [
            'Planimetria',
            'Dati impianto',
            'Documento identità',
            'Libretto impianto',
        ]
    },

    {
        'categoria': 'ENERGIA',
        'nome': 'ENEA',

        'fasi': [
            'Raccolta documentazione',
            'Compilazione portale ENEA',
            'Invio dichiarazione',
            'Archiviazione ricevuta',
        ],

        'checklist': [
            'Fatture',
            'Bonifici',
            'Schede tecniche',
            'Ricevuta ENEA',
        ]
    },

    {
        'categoria': 'SUCCESSIONI_STIME',
        'nome': 'Successione',

        'fasi': [
            'Raccolta documentazione',
            'Verifica eredi',
            'Compilazione successione',
            'Invio telematico',
            'Volture catastali',
        ],

        'checklist': [
            'Certificato morte',
            'Documenti eredi',
            'Visure catastali',
            'Titoli proprietà',
        ]
    },

    {
        'categoria': 'SUCCESSIONI_STIME',
        'nome': 'Perizia di stima',

        'fasi': [
            'Sopralluogo',
            'Raccolta dati',
            'Analisi mercato',
            'Redazione perizia',
            'Consegna relazione',
        ],

        'checklist': [
            'Visura catastale',
            'Documentazione fotografica',
            'OMI',
            'Titolo proprietà',
        ]
    },

    {
        'categoria': 'STRUTTURE',
        'nome': 'Genio Civile',

        'fasi': [
            'Predisposizione elaborati strutturali',
            'Deposito Genio Civile',
            'Monitoraggio istruttoria',
            'Fine lavori strutturali',
            'Collaudo statico',
        ],

        'checklist': [
            'Relazione calcolo',
            'Elaborati strutturali',
            'Relazione geologica',
            'Collaudo',
        ]
    },

    {
        'categoria': 'SICUREZZA_CANTIERI',
        'nome': 'Sicurezza cantieri',

        'fasi': [
            'Nomina CSP/CSE',
            'Predisposizione PSC',
            'Notifica preliminare',
            'Monitoraggio cantiere',
            'Chiusura lavori',
        ],

        'checklist': [
            'PSC',
            'POS',
            'Notifica preliminare',
            'DURC imprese',
        ]
    },

    {
        'categoria': 'CONTABILITA',
        'nome': 'Computo metrico',

        'fasi': [
            'Raccolta elaborati',
            'Misurazioni',
            'Compilazione computo',
            'Verifica prezzi',
            'Consegna computo',
        ],

        'checklist': [
            'Elaborati grafici',
            'Prezziario',
            'Computo metrico',
        ]
    },

]


class Command(BaseCommand):

    help = 'Crea workflow base studio tecnico'

    def handle(self, *args, **kwargs):

        for item in WORKFLOW_BASE:

            workflow, creato = TipoWorkflow.objects.get_or_create(
                nome=item['nome'],
                defaults={
                    'categoria': item['categoria'],
                    'descrizione': item['nome'],
                }
            )

            if creato:

                for i, fase in enumerate(item['fasi'], start=1):

                    FaseWorkflow.objects.create(
                        workflow=workflow,
                        titolo=fase,
                        ordine=i,
                    )

                for i, voce in enumerate(item['checklist'], start=1):

                    ChecklistWorkflow.objects.create(
                        workflow=workflow,
                        voce=voce,
                        ordine=i,
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Creato workflow: {workflow.nome}'
                    )
                )

            else:

                self.stdout.write(
                    self.style.WARNING(
                        f'Workflow già esistente: {workflow.nome}'
                    )
                )