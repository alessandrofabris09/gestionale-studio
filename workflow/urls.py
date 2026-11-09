from django.urls import path

from .views import (
    attiva_workflow_pratica,
    modifica_variante_workflow,
    modelli_workflow,
    toggle_checklist,
    toggle_fase,
)

urlpatterns = [
    path('modelli/', modelli_workflow, name='modelli_workflow'),
    path('modelli/<int:variante_id>/', modifica_variante_workflow, name='modifica_variante_workflow'),
    
    path('checklist/<int:checklist_id>/toggle/', toggle_checklist, name='toggle_checklist'),
    path('fase/<int:fase_id>/toggle/', toggle_fase, name='toggle_fase'),
    path(
        'pratica/<int:pratica_id>/attiva/',
        attiva_workflow_pratica,
        name='attiva_workflow_pratica'
    ),
]
