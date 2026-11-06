from django.core.management.base import BaseCommand

from workflow.models import (
    TipoWorkflow,
    FaseWorkflow,
    ChecklistWorkflow,
)


WORKFLOW_BASE = [

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
        'nome': 'Compravendita',

        'fasi': [
            'Raccolta documentazione',
            'Verifica catastale',
            'Verifica urbanistica',
            'Verifica stato legittimo',
            'Accesso atti',
            'Verifica conformità catastale',
            'Predisposizione documentazione notaio',
            'Assistenza stipula',
            'Archiviazione atto',
        ],

        'checklist': [
            'Documento identità',
            'Codice fiscale',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'Estratto mappa',
            'Stato legittimo',
            'Agibilità',
            'APE',
            'Relazione tecnica integrata',
            'Documentazione notaio',
        ]
    },

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
        'nome': 'Divisione',

        'fasi': [
            'Raccolta documentazione',
            'Verifica quote',
            'Verifica urbanistica',
            'Verifica catastale',
            'Eventuale frazionamento',
            'DOCFA / PREGEO',
            'Predisposizione documenti notaio',
            'Assistenza stipula',
        ],

        'checklist': [
            'Documento identità',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'Estratto mappa',
            'Relazione tecnica',
            'Documentazione notaio',
        ]
    },

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
        'nome': 'Donazione',

        'fasi': [
            'Raccolta documentazione',
            'Verifica urbanistica',
            'Verifica catastale',
            'Verifica stato legittimo',
            'Predisposizione documenti notaio',
            'Assistenza stipula',
        ],

        'checklist': [
            'Documento identità',
            'Titolo proprietà',
            'Visura catastale',
            'Planimetria catastale',
            'APE',
            'Documentazione notaio',
        ]
    },

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
        'nome': 'Successione',

        'fasi': [
            'Raccolta documentazione',
            'Verifica eredi',
            'Verifica patrimonio immobiliare',
            'Compilazione successione',
            'Invio telematico',
            'Volture catastali',
        ],

        'checklist': [
            'Certificato morte',
            'Documenti eredi',
            'Visure catastali',
            'Titoli proprietà',
            'Codici fiscali eredi',
        ]
    },

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
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
            'Planimetria catastale',
        ]
    },

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
        'nome': 'Accesso atti',

        'fasi': [
            'Raccolta delega',
            'Predisposizione richiesta',
            'Deposito richiesta',
            'Ritiro documentazione',
            'Analisi documenti',
        ],

        'checklist': [
            'Documento identità',
            'Delega',
            'Dati catastali',
            'Ricevuta diritti',
        ]
    },

    {
        'categoria': 'PRATICHE_IMMOBILIARI_NOTARILI',
        'nome': 'Relazione tecnica integrata',

        'fasi': [
            'Raccolta documentazione',
            'Verifica urbanistica',
            'Verifica catastale',
            'Verifica stato legittimo',
            'Redazione RTI',
            'Consegna documento',
        ],

        'checklist': [
            'Visura catastale',
            'Planimetria catastale',
            'Titolo edilizio',
            'Agibilità',
            'Documentazione fotografica',
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