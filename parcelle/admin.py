from django import forms
from django.contrib import admin
from django.db import router
from studi.models import Studio
from .models import NumeroDocumentoDuplicato, Parcella


class ParcellaAdminForm(forms.ModelForm):
    def clean(self):
        dati = super().clean()
        pratica = dati.get('pratica')
        numero = (dati.get('numero_documento') or '').strip()
        if not pratica or not numero:
            return dati
        # Django Admin racchiude la validazione e il salvataggio in una transazione.
        using = router.db_for_write(Parcella, instance=self.instance)
        Studio.objects.using(using).select_for_update().get(pk=pratica.studio_id)
        parcelle = Parcella.objects.using(using).filter(
            pratica__studio_id=pratica.studio_id, numero_documento=numero,
        )
        if parcelle.exclude(pk=self.instance.pk).exists() and not parcelle.filter(
            pk=self.instance.pk,
        ).exists():
            self.add_error('numero_documento', NumeroDocumentoDuplicato())
        return dati


@admin.register(Parcella)
class ParcellaAdmin(admin.ModelAdmin):
    form = ParcellaAdminForm
    list_display = (
        'descrizione',
        'pratica',
        'importo',
        'importo_pagato',
        'stato',
        'data_emissione',
    )

    list_filter = (
        'stato',
        'data_emissione',
    )

    search_fields = (
        'descrizione',
        'pratica__oggetto',
        'pratica__cliente__nome',
    )
