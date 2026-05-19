from datetime import timedelta
from io import BytesIO

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.utils.timezone import now

from reportlab.pdfgen import canvas

from workflow.models import (
    TipoWorkflow,
    WorkflowPratica,
    FasePratica,
    ChecklistPratica,
)

from scadenze.models import Scadenza
from attivita.models import Attivita

from .models import Pratica
from .forms import PraticaForm


def attiva_workflow_automatico(pratica):

    workflow = TipoWorkflow.objects.filter(
        nome=pratica.tipo_pratica,
        attivo=True
    ).first()

    if not workflow:
        return None

    workflow_pratica, creato = WorkflowPratica.objects.get_or_create(
        pratica=pratica,
        defaults={
            'workflow': workflow
        }
    )

    if not creato:
        return workflow_pratica

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
                descrizione=f'Workflow automatico: {fase.titolo}',
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

    return workflow_pratica


@login_required
def lista_pratiche(request):

    pratiche = Pratica.objects.all().order_by('-id')

    ricerca = request.GET.get('ricerca')
    stato = request.GET.get('stato')
    tipo = request.GET.get('tipo')

    if ricerca:

        pratiche = pratiche.filter(
            Q(oggetto__icontains=ricerca) |
            Q(comune__icontains=ricerca) |
            Q(protocollo__icontains=ricerca) |
            Q(cliente__nome__icontains=ricerca)
        )

    if stato:
        pratiche = pratiche.filter(
            stato=stato
        )

    if tipo:
        pratiche = pratiche.filter(
            tipo_pratica=tipo
        )

    context = {
        'pratiche': pratiche,
        'ricerca': ricerca,
        'stato': stato,
        'tipo': tipo,
    }

    return render(
        request,
        'pratiche/lista_pratiche.html',
        context
    )


@login_required
def dettaglio_pratica(request, pratica_id):

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    try:
        workflow_pratica = pratica.workflow_pratica
    except Exception:
        workflow_pratica = None

    documenti = pratica.documenti.all()

    parcelle = pratica.parcelle.all()

    attivita = pratica.attivita.all().order_by('-data')

    context = {
        'pratica': pratica,
        'documenti': documenti,
        'parcelle': parcelle,
        'attivita': attivita,
        'workflow_pratica': workflow_pratica,
    }

    return render(
        request,
        'pratiche/dettaglio_pratica.html',
        context
    )


@login_required
def nuova_pratica(request):

    if request.method == 'POST':

        form = PraticaForm(request.POST)

        if form.is_valid():

            pratica = form.save()

            workflow_pratica = attiva_workflow_automatico(pratica)

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='CREAZIONE',
                descrizione=f'Creata pratica: {pratica.oggetto}'
            )

            if workflow_pratica:

                Attivita.objects.create(
                    pratica=pratica,
                    utente=request.user,
                    tipo='AGGIORNAMENTO',
                    descrizione=f'Workflow automatico attivato: {workflow_pratica.workflow.nome}'
                )

            return redirect(
                'dettaglio_pratica',
                pratica_id=pratica.id
            )

    else:

        form = PraticaForm()

    return render(
        request,
        'pratiche/nuova_pratica.html',
        {'form': form}
    )


@login_required
def modifica_pratica(request, pratica_id):

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    if request.method == 'POST':

        form = PraticaForm(
            request.POST,
            instance=pratica
        )

        if form.is_valid():

            pratica = form.save()

            Attivita.objects.create(
                pratica=pratica,
                utente=request.user,
                tipo='MODIFICA',
                descrizione=f'Modificata pratica: {pratica.oggetto}'
            )

            return redirect(
                'dettaglio_pratica',
                pratica_id=pratica.id
            )

    else:

        form = PraticaForm(instance=pratica)

    return render(
        request,
        'pratiche/modifica_pratica.html',
        {
            'form': form,
            'pratica': pratica,
        }
    )


@login_required
def elimina_pratica(request, pratica_id):

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    if request.method == 'POST':

        pratica.delete()

        return redirect(
            'lista_pratiche'
        )

    return render(
        request,
        'pratiche/conferma_eliminazione.html',
        {
            'pratica': pratica
        }
    )


@login_required
def pdf_pratica(request, pratica_id):

    pratica = get_object_or_404(
        Pratica,
        id=pratica_id
    )

    Attivita.objects.create(
        pratica=pratica,
        utente=request.user,
        tipo='PDF',
        descrizione=f'Generato PDF pratica: {pratica.oggetto}'
    )

    buffer = BytesIO()

    p = canvas.Canvas(buffer)

    p.setTitle(f"Scheda pratica {pratica.id}")

    logo_path = "static/img/logo.png"

    y = 790

    try:
        p.drawImage(
            logo_path,
            50,
            765,
            width=90,
            height=45,
            preserveAspectRatio=True,
            mask='auto'
        )
    except Exception:
        pass

    p.setFont("Helvetica-Bold", 18)
    p.drawString(160, 790, "Gestionale Studio Tecnico")

    p.setFont("Helvetica", 10)
    p.drawString(160, 772, "Scheda riepilogativa pratica")

    p.line(50, 750, 545, 750)

    y = 720

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Scheda pratica")

    y -= 35

    def section_title(title, y_pos):

        p.setFillColorRGB(0.07, 0.09, 0.15)

        p.rect(
            50,
            y_pos - 6,
            495,
            24,
            fill=True,
            stroke=False
        )

        p.setFillColorRGB(1, 1, 1)

        p.setFont("Helvetica-Bold", 11)

        p.drawString(60, y_pos, title)

        p.setFillColorRGB(0, 0, 0)

        return y_pos - 35

    def row(label, value, y_pos):

        p.setFont("Helvetica-Bold", 10)

        p.drawString(60, y_pos, f"{label}:")

        p.setFont("Helvetica", 10)

        p.drawString(
            180,
            y_pos,
            str(value) if value else "-"
        )

        return y_pos - 22

    y = section_title("DATI PRATICA", y)

    y = row("ID pratica", pratica.id, y)
    y = row("Tipo pratica", pratica.tipo_pratica, y)
    y = row("Oggetto", pratica.oggetto, y)
    y = row("Stato", pratica.stato, y)
    y = row("Comune", pratica.comune, y)
    y = row("Protocollo", pratica.protocollo, y)

    y -= 10

    y = section_title("CLIENTE E IMMOBILE", y)

    y = row("Cliente", pratica.cliente, y)
    y = row("Immobile", pratica.immobile, y)

    y -= 10

    y = section_title("DATE E SCADENZE", y)

    y = row("Data incarico", pratica.data_incarico, y)
    y = row("Data deposito", pratica.data_deposito, y)
    y = row("Scadenza", pratica.scadenza, y)

    y -= 10

    y = section_title("ASPETTI ECONOMICI", y)

    y = row(
        "Compenso",
        f"Euro {pratica.compenso}" if pratica.compenso else "-",
        y
    )

    y -= 10

    y = section_title("NOTE", y)

    note = str(pratica.note) if pratica.note else "-"

    p.setFont("Helvetica", 10)

    max_chars = 90

    note_lines = [
        note[i:i + max_chars]
        for i in range(0, len(note), max_chars)
    ]

    for line in note_lines:

        if y < 80:
            p.showPage()
            y = 790

        p.drawString(60, y, line)

        y -= 18

    p.line(50, 55, 545, 55)

    p.setFont("Helvetica", 8)

    p.drawString(
        50,
        40,
        "Documento generato automaticamente dal Gestionale Studio Tecnico"
    )

    p.drawRightString(
        545,
        40,
        f"Pratica ID {pratica.id}"
    )

    p.showPage()

    p.save()

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"scheda_pratica_{pratica.id}.pdf"
    )