import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from gestionale.beta_pro import POSTI_BETA


PIANI_STUDIO = [
    ('FREE', 'Free'),
    ('PRO', 'Pro'),
]


STATI_ABBONAMENTO = [
    ('ATTIVO', 'Attivo'),
    ('TRIAL', 'Trial'),
    ('SCADUTO', 'Scaduto'),
    ('ANNULLATO', 'Annullato'),
]


class Studio(models.Model):
    stripe_checkout_pending = models.JSONField(default=dict, blank=True, editable=False)

    nome = models.CharField(max_length=255)

    titolare = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='studi_titolare'
    )

    email = models.EmailField(blank=True)

    telefono = models.CharField(
        max_length=50,
        blank=True
    )

    indirizzo = models.CharField(
        max_length=255,
        blank=True
    )

    partita_iva = models.CharField(
        max_length=50,
        blank=True
    )

    attivo = models.BooleanField(default=True)

    piano = models.CharField(
        max_length=20,
        choices=PIANI_STUDIO,
        default='FREE'
    )

    stato_abbonamento = models.CharField(
        max_length=30,
        choices=STATI_ABBONAMENTO,
        default='TRIAL'
    )

    trial_fino_al = models.DateField(
        null=True,
        blank=True
    )

    abbonamento_scade_il = models.DateField(
        null=True,
        blank=True
    )

    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True
    )

    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True
    )

    calendario_ics_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )

    limite_pratiche = models.PositiveIntegerField(
        default=20
    )

    limite_utenti = models.PositiveIntegerField(
        default=1
    )

    limite_storage_mb = models.PositiveIntegerField(
        default=500
    )

    creato_il = models.DateTimeField(auto_now_add=True)

    aggiornato_il = models.DateTimeField(auto_now=True)

    def genera_calendario_ics_token(self, commit=True):
        """
        Genera un nuovo token segreto per il calendario ICS dello studio.
        """

        self.calendario_ics_token = uuid.uuid4().hex + uuid.uuid4().hex

        if commit:
            self.save(
                update_fields=[
                    'calendario_ics_token',
                    'aggiornato_il',
                ]
            )

        return self.calendario_ics_token

    def get_calendario_ics_token(self):
        """
        Restituisce il token ICS dello studio.
        Se non esiste, lo genera.
        """

        if not self.calendario_ics_token:
            return self.genera_calendario_ics_token()

        return self.calendario_ics_token

    def __str__(self):
        return self.nome

    def is_pro(self):
        return self.ha_piano_pro() or self.fase_beta() in ('ATTIVA', 'LETTURA')

    def ha_piano_pro(self):
        return self.piano == 'PRO' and self.stato_abbonamento in [
            'ATTIVO',
            'TRIAL',
        ]

    def fase_beta(self, oggi=None):
        beta = getattr(self, 'beta_pro', None)
        if beta is None or (self.ha_piano_pro() and self.stato_abbonamento == 'ATTIVO'):
            return None
        oggi = oggi or timezone.localdate()
        if oggi < beta.attivata_il:
            return None
        if oggi < beta.fine_pro_il:
            return 'ATTIVA'
        if oggi < beta.fine_esportazione_il:
            return 'LETTURA'
        return 'CHIUSA'

    def is_free(self):
        return self.piano == 'FREE' and not self.is_pro()

    def trial_attivo(self):

        if not self.trial_fino_al:
            return False

        return self.trial_fino_al >= timezone.now().date()

    def abbonamento_attivo(self):

        if self.fase_beta() == 'ATTIVA':
            return True

        if self.stato_abbonamento == 'TRIAL':
            return self.trial_attivo()

        if self.stato_abbonamento == 'ATTIVO':
            return True

        return False


class BetaStudio(models.Model):
    studio = models.OneToOneField(Studio, on_delete=models.SET_NULL, null=True, related_name='beta_pro')
    posto = models.PositiveSmallIntegerField(unique=True)
    attivata_il = models.DateField()
    fine_pro_il = models.DateField()
    fine_esportazione_il = models.DateField()
    avvisata_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(posto__gte=1, posto__lte=POSTI_BETA),
                name='studi_beta_posto_valido',
            ),
            models.CheckConstraint(
                condition=models.Q(
                    fine_pro_il__gt=models.F('attivata_il'),
                    fine_esportazione_il__gt=models.F('fine_pro_il'),
                ),
                name='studi_beta_date_in_ordine',
            ),
        ]


class ProfiloUtente(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profilo_studio'
    )

    studio = models.ForeignKey(
        Studio,
        on_delete=models.CASCADE,
        related_name='utenti'
    )

    ruolo = models.CharField(
        max_length=50,
        choices=[
            ('TITOLARE', 'Titolare'),
            ('TECNICO', 'Tecnico'),
            ('SEGRETERIA', 'Segreteria'),
            ('COLLABORATORE', 'Collaboratore'),
        ],
        default='TITOLARE'
    )

    def __str__(self):
        return f'{self.user.username} - {self.studio.nome}'
