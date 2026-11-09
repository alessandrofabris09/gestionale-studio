import json

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db.models.deletion import Collector, ProtectedError, RestrictedError

from documenti.models import Documento
from studi.models import Studio


class Command(BaseCommand):
    help = 'Simula la cancellazione di uno studio e mostra soltanto conteggi. Non modifica dati o file.'

    def add_arguments(self, parser):
        parser.add_argument('studio_id', type=int)

    def handle(self, *args, **options):
        try:
            studio = Studio.objects.get(pk=options['studio_id'])
        except Studio.DoesNotExist as exc:
            raise CommandError('Studio non trovato.') from exc

        collector = Collector(using=DEFAULT_DB_ALIAS)
        try:
            collector.collect([studio])
        except (ProtectedError, RestrictedError) as exc:
            raise CommandError('La cancellazione è bloccata da record collegati.') from exc

        record = {
            model._meta.label_lower: len(rows)
            for model, rows in collector.data.items()
        }
        for queryset in collector.fast_deletes:
            label = queryset.model._meta.label_lower
            record[label] = record.get(label, 0) + queryset.count()

        riferimenti_file = (
            Documento.objects.filter(pratica__studio=studio)
            .exclude(file='')
            .values_list('file', flat=True)
            .distinct()
            .count()
        )
        self.stdout.write(json.dumps({
            'studio_id': studio.pk,
            'record_coinvolti': record,
            'percorsi_allegati_da_verificare_nello_storage': riferimenti_file,
            'storage_e_backup_ispezionati': False,
        }, sort_keys=True))
