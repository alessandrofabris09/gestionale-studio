import json
from os import link
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documenti.models import Documento


class Command(BaseCommand):
    help = 'Copia gli allegati di tutti gli studi in uno ZIP privato fuori dal progetto.'

    def add_arguments(self, parser):
        parser.add_argument('destinazione', type=Path)

    def handle(self, *args, **options):
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
                    for documento in Documento.objects.only('file').order_by('pk').iterator():
                        voce = f'allegati/{documento.pk}'
                        try:
                            with documento.file.open('rb') as origine:
                                with archivio.open(voce, 'w', force_zip64=True) as copia:
                                    copyfileobj(origine, copia)
                        except Exception as exc:
                            raise CommandError(f'Impossibile copiare il documento {documento.pk}. Archivio non pubblicato.') from exc
                        indice.append({'id': documento.pk, 'file': documento.file.name, 'voce_zip': voce})
                    archivio.writestr('indice.json', json.dumps(indice, ensure_ascii=False))

                with ZipFile(temporaneo) as archivio:
                    if archivio.testzip() is not None:
                        raise CommandError('Verifica integrità ZIP fallita.')
                # Pubblica il file completo senza sovrascrivere un archivio esistente.
                link(temporaneo, destinazione)
        except OSError as exc:
            raise CommandError(f'Impossibile scrivere l’archivio: {exc}') from exc

        self.stdout.write(self.style.SUCCESS(f'Allegati copiati e verificati: {len(indice)}'))
