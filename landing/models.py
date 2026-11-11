from django.db import models

class IscrizioneFreeLancio(models.Model):
    studio = models.OneToOneField('studi.Studio', on_delete=models.CASCADE)
    iscritta_il = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('iscritta_il', 'pk')
        verbose_name = 'iscrizione Free al lancio'
        verbose_name_plural = 'iscrizioni Free al lancio'

    @classmethod
    def attive(cls):
        return cls.objects.filter(studio__attivo=True)
