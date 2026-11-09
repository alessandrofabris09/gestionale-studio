from django.db import models, router, transaction

from clienti.models import Cliente
from immobili.models import Immobile
from studi.models import Studio


TIPI_PRATICA = [
    ('CILA', 'CILA'),
    ('SCIA', 'SCIA'),
    ('PDC', 'Permesso di Costruire'),
    ('SANATORIA', 'Sanatoria'),
    ('PAESAGGISTICA', 'Paesaggistica'),
    ('CATASTO', 'Catasto'),
    ('FRAZIONAMENTO', 'Frazionamento'),
    ('SUCCESSIONE', 'Successione'),
    ('APE', 'APE'),
    ('PERIZIA', 'Perizia'),
]


STATI_PRATICA = [
    ('PREVENTIVO', 'Preventivo'),
    ('IN_CORSO', 'In corso'),
    ('DEPOSITATA', 'Depositata'),
    ('INTEGRAZIONE', 'Integrazione'),
    ('APPROVATA', 'Approvata'),
    ('CONCLUSA', 'Conclusa'),
]


class Pratica(models.Model):

    studio = models.ForeignKey(
        Studio,
        on_delete=models.CASCADE,
        related_name='pratiche'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE
    )

    immobile = models.ForeignKey(
        Immobile,
        on_delete=models.CASCADE
    )

    tipo_pratica = models.CharField(
        max_length=255
    )

    stato = models.CharField(
        max_length=50,
        choices=STATI_PRATICA,
        default='IN_CORSO'
    )

    oggetto = models.CharField(max_length=255)

    comune = models.CharField(max_length=150)

    protocollo = models.CharField(
        max_length=100,
        blank=True
    )

    data_incarico = models.DateField(
        null=True,
        blank=True
    )

    data_deposito = models.DateField(
        null=True,
        blank=True
    )

    scadenza = models.DateField(
        null=True,
        blank=True
    )

    compenso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    scadenza_compenso = models.DateField(null=True, blank=True)

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        campi = kwargs.get('update_fields')
        if campi is not None and not {'scadenza', 'stato'}.intersection(campi):
            return super().save(*args, **kwargs)

        from scadenze.models import Scadenza

        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        with transaction.atomic(using=using):
            super().save(*args, **kwargs)
            pratica = self
            if campi is not None:
                pratica = type(self).objects.using(using).only('scadenza', 'stato').get(pk=self.pk)
            promemoria = Scadenza.objects.using(using)
            if pratica.scadenza:
                promemoria.update_or_create(pratica_id=self.pk, da_pratica=True, defaults={
                    'titolo': 'Scadenza pratica',
                    'data_scadenza': pratica.scadenza,
                    'completata': pratica.stato == 'CONCLUSA',
                    'archiviata': False,
                })
            else:
                promemoria.filter(pratica_id=self.pk, da_pratica=True, archiviata=False).update(archiviata=True)

    def __str__(self):
        return f"{self.tipo_pratica} - {self.oggetto}"
