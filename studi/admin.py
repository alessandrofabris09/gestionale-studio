from django.contrib import admin

from .models import Studio, ProfiloUtente


@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'titolare',
        'email',
        'telefono',
        'attivo',
        'creato_il',
    )

    search_fields = (
        'nome',
        'email',
        'partita_iva',
        'titolare__username',
    )

    list_filter = (
        'attivo',
        'creato_il',
    )


@admin.register(ProfiloUtente)
class ProfiloUtenteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'studio',
        'ruolo',
    )

    search_fields = (
        'user__username',
        'studio__nome',
    )

    list_filter = (
        'ruolo',
        'studio',
    )