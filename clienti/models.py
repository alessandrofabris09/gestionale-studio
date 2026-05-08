from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    telefono = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    pec = models.EmailField(blank=True)
    codice_fiscale = models.CharField(max_length=16, blank=True)
    partita_iva = models.CharField(max_length=20, blank=True)
    indirizzo = models.TextField(blank=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.nome