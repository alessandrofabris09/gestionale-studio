from django.contrib import admin
from .models import Parcella


@admin.register(Parcella)
class ParcellaAdmin(admin.ModelAdmin):
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