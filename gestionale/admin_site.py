from django.contrib.admin import AdminSite


class PlatformAdminSite(AdminSite):
    """Il pannello globale e riservato agli amministratori senza studio."""

    def has_permission(self, request):
        from studi.utils import is_admin_piattaforma
        return super().has_permission(request) and is_admin_piattaforma(request)
