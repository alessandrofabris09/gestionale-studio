from django.contrib import admin

from .models import IscrizioneFreeLancio


@admin.register(IscrizioneFreeLancio)
class IscrizioneFreeLancioAdmin(admin.ModelAdmin):
    list_display = ('studio', 'iscritta_il')
    list_select_related = ('studio',)
    readonly_fields = ('studio', 'iscritta_il')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(studio__attivo=True)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
