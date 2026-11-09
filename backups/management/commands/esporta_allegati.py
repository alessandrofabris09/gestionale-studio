import json
from os import link
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError

from agenda.models import EventoAgenda
from attivita.models import Attivita
from clienti.models import Cliente
from documenti.models import Documento
from immobili.models import Immobile
from ore.models import VoceOra
from parcelle.models import Incasso, Parcella
from pratiche.models import Pratica
from scadenze.models import Scadenza
from studi.models import Studio
from workflow.models import ChecklistPratica, FasePratica, WorkflowPratica


def dati_operativi(studio_id):
    percorsi = (
        (Cliente, 'studio_id'),
        (Immobile, 'studio_id'),
        (Pratica, 'studio_id'),
        (EventoAgenda, 'studio_id'),
        (Documento, 'pratica__studio_id'),
        (Attivita, 'pratica__studio_id'),
        (VoceOra, 'pratica__studio_id'),
        (Parcella, 'pratica__studio_id'),
        (Incasso, 'parcella__pratica__studio_id'),
        (Scadenza, 'pratica__studio_id'),
        (WorkflowPratica, 'pratica__studio_id'),
        (FasePratica, 'workflow_pratica__pratica__studio_id'),
        (ChecklistPratica, 'workflow_pratica__pratica__studio_id'),
    )
    for modello, percorso in percorsi:
        yield from modello.objects.filter(**{percorso: studio_id}).order_by('pk').iterator()


class Command(BaseCommand):
    help = 'Copia gli allegati di tutti gli studi in uno ZIP privato fuori dal progetto.'

    def add_arguments(self, parser):
        parser.add_argument('destinazione', type=Path)
        parser.add_argument('--studio-id', type=int, help='Esporta gli allegati e i dati operativi dello studio indicato.')

    def handle(self, *args, **options):
        documenti = Documento.objects.only('file').order_by('pk')
        studio_id = options['studio_id']
        if studio_id is not None:
            if not Studio.objects.filter(pk=studio_id).exists():
                raise CommandError('Studio non trovato.')
            documenti = documenti.filter(pratica__studio_id=studio_id)

        destinazione = options['destinazione'].resolve()
        if (
            destinazione.suffix.lower() != '.zip'
            or destinazione.is_relative_to(Path(settings.BASE_DIR).resolve())
            or destinazione.is_relative_to(Path(settings.MEDIA_ROOT).resolve())
            or not destinazione.parent.is_dir()
        ):
            raise CommandError('Indica un nuovo file .zip in una cartella privata esistente fuori dal progetto e dai media.')
        if destinazione.exists():
            raise CommandError('Il file di destinazione esiste già.')

        indice = []
        try:
            with TemporaryDirectory(dir=destinazione.parent) as cartella:
                temporaneo = Path(cartella) / 'allegati.zip'
                with ZipFile(temporaneo, 'w', compression=ZIP_DEFLATED) as archivio:
                    for documento in documenti.iterator():
                        voce = f'allegati/{documento.pk}'
                        try:
                            with documento.file.open('rb') as origine:
                                with archivio.open(voce, 'w', force_zip64=True) as copia:
                                    copyfileobj(origine, copia)
                        except Exception as exc:
                            raise CommandError(f'Impossibile copiare il documento {documento.pk}. Archivio non pubblicato.') from exc
                        indice.append({'id': documento.pk, 'file': documento.file.name, 'voce_zip': voce})
                    archivio.writestr('indice.json', json.dumps(indice, ensure_ascii=False))
                    if studio_id is not None:
                        with archivio.open('dati-operativi.json', 'w', force_zip64=True) as voce:
                            from io import TextIOWrapper
                            with TextIOWrapper(voce, encoding='utf-8') as stream:
                                serializers.serialize('json', dati_operativi(studio_id), stream=stream)

                with ZipFile(temporaneo) as archivio:
                    if archivio.testzip() is not None:
                        raise CommandError('Verifica integrità ZIP fallita.')
                # Pubblica il file completo senza sovrascrivere un archivio esistente.
                link(temporaneo, destinazione)
        except OSError as exc:
            raise CommandError(f'Impossibile scrivere l’archivio: {exc}') from exc

        self.stdout.write(self.style.SUCCESS(f'Allegati copiati e verificati: {len(indice)}'))
