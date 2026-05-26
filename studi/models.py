from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    def __str__(self):
        return self.nome

    def is_pro(self):
        return self.piano == 'PRO' and self.stato_abbonamento in [
            'ATTIVO',
            'TRIAL',
        ]

    def is_free(self):
        return self.piano == 'FREE'

    def trial_attivo(self):

        if not self.trial_fino_al:
            return False

        return self.trial_fino_al >= timezone.now().date()

    def abbonamento_attivo(self):

        if self.stato_abbonamento == 'TRIAL':
            return self.trial_attivo()

        if self.stato_abbonamento == 'ATTIVO':
            return True

        return False


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