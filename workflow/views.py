from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now

from pratiche.models import Pratica
from scadenze.models import Scadenza
from attivita.models import Attivita

from .models import (
    WorkflowPratica,
    FasePratica,
    ChecklistPratica,
)

from .forms import WorkflowPraticaForm


@login_required
def attiva_workflow_pratica(request, pratica_id):

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    workflow_pratica, creato = WorkflowPratica.objects.get_or_create(
        pratica=pratica
    )

    if request.method == 'POST':

        form = WorkflowPraticaForm(
            request.POST,
            instance=workflow_pratica
        )

        if form.is_valid():

            workflow_pratica = form.save(commit=False)
            workflow_pratica.pratica = pratica
            workflow_pratica.save()

            workflow = workflow_pratica.workflow

            FasePratica.objects.filter(
                workflow_pratica=workflow_pratica
            ).delete()

            ChecklistPratica.objects.filter(
                workflow_pratica=workflow_pratica
            ).delete()

            for fase in workflow.fasi.all().order_by('ordine'):

                data_scadenza = None

                if fase.giorni_scadenza:
                    data_scadenza = now().date() + timedelta(
                        days=fase.giorni_scadenza
                    )

                FasePratica.objects.create(
                    workflow_pratica=workflow_pratica,
                    titolo=fase.titolo,
                    descrizione=fase.descrizione,
                    ordine=fase.ordine,
                    data_scadenza=data_scadenza
                )

                if data_scadenza:
                    Scadenza.objects.create(
                        pratica=pratica,
                        titolo=fase.titolo,
                        descrizione=f'Fase workflow: {fase.titolo}',
                        data_scadenza=data_scadenza,
                        completata=False
                    )

            for voce in workflow.checklist.all().order_by('ordine'):

                ChecklistPratica.objects.create(
                    workflow_pratica=workflow_pratica,
                    voce=voce.voce,
                    descrizione=voce.descrizione,
                    obbligatorio=voce.obbligatorio,
                    ordine=voce.ordine
                )

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='AGGIORNAMENTO',
                descrizione=f'Attivato workflow: {workflow.nome}'
            )

            return redirect(
                'dettaglio_pratica',
                pratica_id=pratica.id
            )

    else:

        form = WorkflowPraticaForm(instance=workflow_pratica)

    return render(
        request,
        'workflow/attiva_workflow.html',
        {
            'form': form,
            'pratica': pratica,
        }
    )

@login_required
def toggle_checklist(request, checklist_id):

    checklist = get_object_or_404(
        ChecklistPratica,
        id=checklist_id
    )

    checklist.completato = not checklist.completato
    checklist.save()

    return redirect(
        'dettaglio_pratica',
        pratica_id=checklist.workflow_pratica.pratica.id
    )

@login_required
def toggle_fase(request, fase_id):

    fase = get_object_or_404(
        FasePratica,
        id=fase_id
    )

    fase.completata = not fase.completata
    fase.save()

    return redirect(
        'dettaglio_pratica',
        pratica_id=fase.workflow_pratica.pratica.id
    )