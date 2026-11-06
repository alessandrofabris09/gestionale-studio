from django.urls import path

from .views import (
    attiva_workflow_pratica,
    toggle_checklist,
    toggle_fase,
)

urlpatterns = [
    
    path('checklist/<int:checklist_id>/toggle/', toggle_checklist, name='toggle_checklist'),
    path('fase/<int:fase_id>/toggle/', toggle_fase, name='toggle_fase'),
    path(
        'pratica/<int:pratica_id>/attiva/',
        attiva_workflow_pratica,
        name='attiva_workflow_pratica'
    ),
]