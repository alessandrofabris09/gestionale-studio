from django.db import transaction
from django.views.decorators.http import require_POST
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now

from studi.utils import get_studio_utente
from studi.permessi import puo_modificare_pratiche

from pratiche.models import Pratica
from scadenze.models import Scadenza
from attivita.models import Attivita

from .models import (
    WorkflowPratica,
    FasePratica,
    ChecklistPratica,
)

from .forms import WorkflowPraticaForm


def accesso_negato(request):
    """
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )


@login_required
@transaction.atomic
def attiva_workflow_pratica(request, pratica_id):

    if not puo_modificare_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio:
        return redirect('login')

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id,
        studio=studio
    )

    if request.method == 'POST':
        # Il blocco della pratica serializza anche la prima attivazione concorrente.
        Pratica.objects.select_for_update().get(pk=pratica.pk)

    workflow_pratica = WorkflowPratica.objects.filter(pratica=pratica).first()
    if workflow_pratica is None:
        workflow_pratica = WorkflowPratica(pratica=pratica)
    workflow_precedente_id = workflow_pratica.workflow_id

    if request.method == 'POST':

        form = WorkflowPraticaForm(
            request.POST,
            instance=workflow_pratica
        )

        if form.is_valid():

            # Ripetere lo stesso procedimento aggiorna le note senza cancellare
            # i progressi e senza generare nuove scadenze.
            if workflow_pratica.pk and workflow_precedente_id == form.cleaned_data['workflow'].pk:
                workflow_pratica.note = form.cleaned_data.get('note', '')
                workflow_pratica.save(update_fields=['note'])
                return redirect('dettaglio_pratica', pratica_id=pratica.pk)

            # Mantiene lo storico e toglie dagli avvisi solo le scadenze
            # sicuramente generate da questa attivazione.
            if workflow_pratica.pk:
                Scadenza.objects.filter(
                    workflow_origine=workflow_pratica, archiviata=False,
                ).update(archiviata=True)

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

            if workflow:

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
                            workflow_origine=workflow_pratica,
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

        form = WorkflowPraticaForm(
            instance=workflow_pratica
        )

    return render(
        request,
        'workflow/attiva_workflow.html',
        {
            'form': form,
            'pratica': pratica,
        }
    )


@login_required
@require_POST
def toggle_checklist(request, checklist_id):

    if not puo_modificare_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio:
        return redirect('login')

    checklist = get_object_or_404(
        ChecklistPratica,
        id=checklist_id,
        workflow_pratica__pratica__studio=studio
    )

    checklist.completato = not checklist.completato
    checklist.save()

    return redirect(
        'dettaglio_pratica',
        pratica_id=checklist.workflow_pratica.pratica.id
    )


@login_required
@require_POST
def toggle_fase(request, fase_id):

    if not puo_modificare_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio:
        return redirect('login')

    fase = get_object_or_404(
        FasePratica,
        id=fase_id,
        workflow_pratica__pratica__studio=studio
    )

    fase.completata = not fase.completata
    fase.save()

    return redirect(
        'dettaglio_pratica',
        pratica_id=fase.workflow_pratica.pratica.id
    )