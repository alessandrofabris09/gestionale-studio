from django.db import transaction
from django.views.decorators.http import require_POST, require_http_methods
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.timezone import now

from studi.utils import get_studio_utente
from studi.permessi import is_titolare, puo_modificare_pratiche

from pratiche.models import Pratica
from scadenze.models import Scadenza
from attivita.models import Attivita

from .models import (
    TipoWorkflow,
    FaseWorkflow,
    ChecklistWorkflow,
    WorkflowPratica,
    FasePratica,
    ChecklistPratica,
)

from .forms import (
    ChecklistVariante, CopiaModelloForm, FasiVariante, VarianteWorkflowForm, WorkflowPraticaForm,
)


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
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def modelli_workflow(request):
    studio = get_studio_utente(request)
    if not studio or not is_titolare(request):
        return accesso_negato(request)

    disponibili = TipoWorkflow.objects.disponibili_per(studio)
    standard = disponibili.filter(studio__isnull=True)
    form = CopiaModelloForm(request.POST if request.method == 'POST' else None, standard=standard)
    if request.method == 'POST' and form.is_valid():
        base = form.cleaned_data['modello']
        variante = TipoWorkflow.objects.create(
            studio=studio, categoria=base.categoria, nome=base.nome,
            descrizione=base.descrizione, ordine=base.ordine, attivo=False,
        )
        FaseWorkflow.objects.bulk_create([
            FaseWorkflow(workflow=variante, **valori)
            for valori in base.fasi.values('titolo', 'descrizione', 'ordine', 'giorni_scadenza')
        ])
        ChecklistWorkflow.objects.bulk_create([
            ChecklistWorkflow(workflow=variante, **valori)
            for valori in base.checklist.values('voce', 'descrizione', 'ordine', 'obbligatorio')
        ])
        return redirect('modifica_variante_workflow', variante_id=variante.pk)

    return render(request, 'workflow/modelli.html', {
        'form': form,
        'varianti': TipoWorkflow.objects.filter(studio=studio).order_by('nome', 'pk'),
    })


@login_required
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def modifica_variante_workflow(request, variante_id):
    studio = get_studio_utente(request)
    if not studio or not is_titolare(request):
        return accesso_negato(request)

    varianti = TipoWorkflow.objects.filter(studio=studio)
    if request.method == 'POST':
        varianti = varianti.select_for_update()
    variante = get_object_or_404(varianti, pk=variante_id)
    dati = request.POST if request.method == 'POST' else None
    form = VarianteWorkflowForm(dati, instance=variante)
    fasi = FasiVariante(dati, instance=variante, queryset=variante.fasi.order_by('ordine', 'pk'))
    checklist = ChecklistVariante(
        dati, instance=variante, queryset=variante.checklist.order_by('ordine', 'pk'),
    )
    if request.method == 'POST':
        validi = [form.is_valid(), fasi.is_valid(), checklist.is_valid()]
        if all(validi):
            variante.attivo = True
            form.save()
            fasi.save()
            checklist.save()
            return redirect('modelli_workflow')

    return render(request, 'workflow/variante.html', {
        'form': form, 'fasi': fasi, 'checklist': checklist,
    })


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
            instance=workflow_pratica,
            studio=studio,
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

                    fase_pratica = FasePratica.objects.create(
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
                            fase_origine=fase_pratica,
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
            instance=workflow_pratica,
            studio=studio,
        )

    return render(
        request,
        'workflow/attiva_workflow.html',
        {
            'form': form,
            'pratica': pratica,
            'gestisce_modelli': is_titolare(request),
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

    return redirect(reverse(
        'dettaglio_pratica',
        kwargs={'pratica_id': checklist.workflow_pratica.pratica_id},
        fragment=f'checklist-{checklist.pk}',
    ))


@login_required
@require_POST
@transaction.atomic
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
    pratica_id = fase.workflow_pratica.pratica_id
    # Usa lo stesso blocco della sostituzione del workflow.
    get_object_or_404(Pratica.objects.select_for_update(), pk=pratica_id, studio=studio)
    fase = get_object_or_404(FasePratica, pk=fase_id, workflow_pratica__pratica_id=pratica_id)

    fase.completata = not fase.completata
    fase.save(update_fields=['completata'])
    Scadenza.objects.filter(fase_origine=fase, archiviata=False).update(completata=fase.completata)

    return redirect(reverse(
        'dettaglio_pratica',
        kwargs={'pratica_id': pratica_id},
        fragment=f'fase-{fase.pk}',
    ))
