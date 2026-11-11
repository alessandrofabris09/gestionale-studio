from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError

from .beta_pro import attiva_beta_pro
from .models import Studio, ProfiloUtente
from .utils import is_admin_piattaforma


@admin.register(Studio)
class StudioAdmin(admin.ModelAdmin):
    actions = ('ammetti_alla_beta',)
    list_select_related = ('titolare', 'beta_pro')
    list_display = (
        'nome',
        'titolare',
        'email',
        'telefono',
        'attivo',
        'fase_beta',
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

    @admin.action(description='Attiva la beta PRO per gli studi selezionati')
    def ammetti_alla_beta(self, request, queryset):
        if not is_admin_piattaforma(request):
            raise PermissionDenied
        for studio in queryset.order_by('pk'):
            try:
                beta, creata = attiva_beta_pro(studio.pk)
            except ValidationError as exc:
                self.message_user(request, f'{studio.nome} — {exc.messages[0]}', messages.ERROR)
                continue
            if creata:
                self.message_user(request, f'{studio.nome} — Posto {beta.posto} assegnato.')
            else:
                self.message_user(request, f'{studio.nome} — L’ammissione è già registrata.')


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
