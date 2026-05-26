from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [

    path('studi/', include('studi.urls')),
    
    path('', include('landing.urls')),

    path('dashboard/', include('dashboard.urls')),

    path('login/', auth_views.LoginView.as_view(), name='login'),     
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('clienti/', include('clienti.urls')),

    path('immobili/', include('immobili.urls')),

    path('pratiche/', include('pratiche.urls')),

    path('documenti/', include('documenti.urls')),

    path('scadenze/', include('scadenze.urls')),

    path('parcelle/', include('parcelle.urls')),

    path('agenda/', include('agenda.urls')),

    path('workflow/', include('workflow.urls')),

    path('utenti/', include('utenti.urls')),

    path('backups/', include('backups.urls')),

    path('admin/', admin.site.urls),

    path('billing/', include('billing.urls')),

]

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )