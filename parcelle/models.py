from decimal import Decimal

from django.db import models
from django.utils import timezone

from pratiche.models import Pratica


STATO_PAGAMENTO = [
    ('DA_PAGARE', 'Da pagare'),
    ('PARZIALE', 'Parziale'),
    ('PAGATO', 'Pagato'),
]


TIPO_DOCUMENTO = [
    ('PREVENTIVO', 'Preventivo'),
    ('PARCELLA', 'Parcella'),
    ('FATTURA', 'Fattura'),
]


TIPO_CASSA = [
    ('NESSUNA', 'Nessuna cassa'),
    ('GEOMETRI', 'Geometri / Cassa Geometri'),
    ('INARCASSA', 'Architetti-Ingegneri / Inarcassa'),
    ('EPPI', 'Periti Industriali / EPPI'),
    ('MANUALE', 'Altro / Manuale'),
]


ALIQUOTE_CASSA_STANDARD = {
    'NESSUNA': Decimal('0.00'),
    'GEOMETRI': Decimal('5.00'),
    'INARCASSA': Decimal('4.00'),
    'EPPI': Decimal('5.00'),
    'MANUALE': Decimal('0.00'),
}


class Parcella(models.Model):

    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='parcelle'
    )

    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO,
        default='PARCELLA'
    )

    numero_documento = models.CharField(
        max_length=50,
        blank=True
    )

    descrizione = models.CharField(
        max_length=255
    )

    importo = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    importo_pagato = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    applica_cassa = models.BooleanField(
        default=True
    )

    tipo_cassa = models.CharField(
        max_length=30,
        choices=TIPO_CASSA,
        default='GEOMETRI'
    )

    aliquota_cassa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5
    )

    applica_iva = models.BooleanField(
        default=True
    )

    iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=22
    )

    applica_bollo = models.BooleanField(
        default=False
    )

    importo_bollo = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=2
    )

    data_emissione = models.DateField(
        null=True,
        blank=True
    )

    data_scadenza = models.DateField(
        null=True,
        blank=True
    )

    data_pagamento = models.DateField(
        null=True,
        blank=True
    )

    stato = models.CharField(
        max_length=20,
        choices=STATO_PAGAMENTO,
        default='DA_PAGARE'
    )

    note = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            '-data_emissione',
            '-created_at',
            '-id',
        ]

    def save(self, *args, **kwargs):
        """
        Compila automaticamente:
        - numero documento, se mancante
        - data emissione, se mancante
        - aliquote standard, se non impostate
        - stato pagamento in base agli importi
        """

        if not self.data_emissione:
            self.data_emissione = timezone.now().date()

        self.normalizza_aliquote()

        if not self.numero_documento or self.numero_documento.strip() == '':

            anno = timezone.now().year

            prefisso = self.get_prefisso_documento()

            ultimo_numero = Parcella.objects.filter(
                tipo_documento=self.tipo_documento,
                data_emissione__year=anno
            ).count() + 1

            self.numero_documento = (
                f'{prefisso}-{anno}-{ultimo_numero:04d}'
            )

        self.aggiorna_stato_pagamento()

        super().save(*args, **kwargs)

    def normalizza_aliquote(self):
        """
        Imposta valori coerenti per IVA, cassa e bollo.
        """

        if self.importo is None:
            self.importo = Decimal('0.00')

        if self.importo_pagato is None:
            self.importo_pagato = Decimal('0.00')

        if not self.applica_cassa:
            self.tipo_cassa = 'NESSUNA'
            self.aliquota_cassa = Decimal('0.00')

        else:

            if not self.tipo_cassa:
                self.tipo_cassa = 'GEOMETRI'

            if self.aliquota_cassa is None or self.aliquota_cassa == Decimal('0.00'):

                self.aliquota_cassa = ALIQUOTE_CASSA_STANDARD.get(
                    self.tipo_cassa,
                    Decimal('0.00')
                )

        if self.iva is None:
            self.iva = Decimal('22.00')

        if self.importo_bollo is None:
            self.importo_bollo = Decimal('2.00')

    def get_prefisso_documento(self):
        """
        Restituisce il prefisso corretto in base al tipo documento.
        """

        if self.tipo_documento == 'PREVENTIVO':
            return 'PRE'

        if self.tipo_documento == 'PARCELLA':
            return 'PAR'

        if self.tipo_documento == 'FATTURA':
            return 'FAT'

        return 'DOC'

    @property
    def imponibile(self):
        """
        Compenso professionale base, esclusi cassa, IVA e bollo.
        """

        return self.importo or Decimal('0.00')

    @property
    def importo_cassa(self):
        """
        Contributo cassa calcolato sull'imponibile base.
        """

        if not self.applica_cassa:
            return Decimal('0.00')

        aliquota = self.aliquota_cassa or Decimal('0.00')

        return self.imponibile * aliquota / Decimal('100.00')

    @property
    def imponibile_iva(self):
        """
        Base imponibile IVA:
        compenso + eventuale contributo cassa.
        """

        return self.imponibile + self.importo_cassa

    @property
    def importo_iva(self):
        """
        IVA calcolata sull'imponibile IVA.
        """

        if not self.applica_iva:
            return Decimal('0.00')

        iva = self.iva or Decimal('0.00')

        return self.imponibile_iva * iva / Decimal('100.00')

    @property
    def importo_bollo_effettivo(self):
        """
        Marca da bollo applicata solo se selezionata.
        """

        if not self.applica_bollo:
            return Decimal('0.00')

        return self.importo_bollo or Decimal('0.00')

    @property
    def totale_documento(self):
        """
        Totale documento:
        imponibile + cassa + IVA + bollo.
        """

        return (
            self.imponibile_iva +
            self.importo_iva +
            self.importo_bollo_effettivo
        )

    @property
    def totale_con_iva(self):
        """
        Compatibilità con il vecchio codice.
        Ora restituisce il totale documento completo.
        """

        return self.totale_documento

    @property
    def saldo_residuo(self):
        """
        Importo ancora da incassare.
        """

        pagato = self.importo_pagato or Decimal('0.00')

        return self.totale_documento - pagato

    def aggiorna_stato_pagamento(self):
        """
        Aggiorna automaticamente lo stato del pagamento.
        """

        pagato = self.importo_pagato or Decimal('0.00')
        totale = self.totale_documento

        if pagato <= Decimal('0.00'):
            self.stato = 'DA_PAGARE'

        elif pagato < totale:
            self.stato = 'PARZIALE'

        else:
            self.stato = 'PAGATO'

            if not self.data_pagamento:
                self.data_pagamento = timezone.now().date()

    def __str__(self):
        numero = (
            self.numero_documento
            if self.numero_documento
            else 'Documento non numerato'
        )

        return f'{numero} - {self.descrizione}'