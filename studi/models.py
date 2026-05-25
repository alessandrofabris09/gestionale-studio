from django.db import models
from django.contrib.auth.models import User


class Studio(models.Model):

    nome = models.CharField(max_length=255)

    titolare = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='studi_titolare'
    )

    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    indirizzo = models.CharField(max_length=255, blank=True)
    partita_iva = models.CharField(max_length=50, blank=True)

    attivo = models.BooleanField(default=True)

    creato_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


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