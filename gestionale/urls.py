from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('', include('dashboard.urls')),

    path('clienti/', include('clienti.urls')),

    path('immobili/', include('immobili.urls')),

    path('pratiche/', include('pratiche.urls')),

    path('documenti/', include('documenti.urls')),

    path('scadenze/', include('scadenze.urls')),

    path('admin/', admin.site.urls),

    path('parcelle/', include('parcelle.urls')),

    path('', include('accounts.urls')),

    path('backups/', include('backups.urls')),

    path('agenda/', include('agenda.urls')),

    path('workflow/', include('workflow.urls')),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )