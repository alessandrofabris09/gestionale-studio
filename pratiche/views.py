from datetime import timedelta
from io import BytesIO

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.contrib import messages

from django.http import FileResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

from studi.utils import get_studio_utente, studio_puo_creare_pratiche

from studi.permessi import (
    puo_creare_pratiche,
    puo_modificare_pratiche,
    puo_eliminare_pratiche,
    puo_gestire_documenti,
)

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


def accesso_negato(request):
    """
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )


def puo_vedere_area_pratiche(request):
    """
    Può vedere l'area pratiche chi può creare pratiche
    oppure chi può gestire documenti.

    In pratica:
    - TITOLARE
    - TECNICO
    - SEGRETERIA, se abilitata ai documenti
    - SUPERUSER
    """

    return (
        puo_creare_pratiche(request) or
        puo_gestire_documenti(request)
    )


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

    if not puo_vedere_area_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.user.is_superuser:
        pratiche = Pratica.objects.all().order_by('-id')
    else:
        pratiche = Pratica.objects.filter(
            studio=studio
        ).order_by('-id')

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

    if not puo_vedere_area_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id
        )
    else:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id,
            studio=studio
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

    if not puo_creare_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if not request.user.is_superuser:

        if not studio_puo_creare_pratiche(studio):

            return render(
                request,
                'studi/upgrade_required.html',
                {
                    'studio': studio,
                    'titolo': 'Limite pratiche raggiunto',
                    'messaggio': (
                        f'Il piano FREE consente di creare massimo '
                        f'{studio.limite_pratiche} pratiche. '
                        f'Per continuare a creare nuove pratiche passa al piano PRO.'
                    ),
                    'azione': 'Passa al piano PRO',
                }
            )

    if request.method == 'POST':

        form = PraticaForm(
            request.POST,
            studio=studio
        )

        if form.is_valid():

            pratica = form.save(commit=False)
            pratica.studio = studio
            pratica.save()

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

        form = PraticaForm(
            studio=studio
        )

    return render(
        request,
        'pratiche/nuova_pratica.html',
        {
            'form': form
        }
    )


@login_required
def modifica_pratica(request, pratica_id):

    if not puo_modificare_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id
        )
    else:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id,
            studio=studio
        )

    if request.method == 'POST':

        form = PraticaForm(
            request.POST,
            instance=pratica,
            studio=studio
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

        form = PraticaForm(
            instance=pratica,
            studio=studio
        )

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

    if not puo_eliminare_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id
        )
    else:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id,
            studio=studio
        )

    if request.method == 'POST':

        Attivita.objects.create(
            pratica=pratica,
            utente=request.user,
            tipo='ELIMINAZIONE',
            descrizione=f'Eliminata pratica: {pratica.oggetto}'
        )

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


def data_it(value):
    """
    Formatta una data in formato italiano.
    """

    if not value:
        return "-"

    return value.strftime('%d/%m/%Y')


def euro(value):
    """
    Formatta un importo in euro.
    """

    if value is None:
        return "-"

    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def testo(value):
    """
    Restituisce testo sicuro per il PDF.
    """

    if value is None or value == '':
        return "-"

    return str(value)


def draw_wrapped_text(
    p,
    text,
    x,
    y,
    max_width,
    font_name="Helvetica",
    font_size=9,
    line_height=12,
    min_y=70
):
    """
    Scrive testo multilinea entro una larghezza massima.
    Se finisce lo spazio, interrompe con puntini.
    """

    p.setFont(font_name, font_size)

    if not text:
        text = "-"

    words = str(text).split()
    line = ""

    for word in words:

        test_line = f"{line} {word}".strip()

        if p.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line

        else:

            if y <= min_y:
                p.drawString(x, y, "...")
                return y - line_height

            p.drawString(x, y, line)
            y -= line_height
            line = word

    if line and y > min_y:
        p.drawString(x, y, line)
        y -= line_height

    return y


@login_required
def pdf_pratica(request, pratica_id):

    if not puo_vedere_area_pratiche(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id
        )
    else:
        pratica = get_object_or_404(
            Pratica,
            id=pratica_id,
            studio=studio
        )

    Attivita.objects.create(
        pratica=pratica,
        utente=request.user,
        tipo='PDF',
        descrizione=f'Generato PDF pratica: {pratica.oggetto}'
    )

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    margin_x = 20 * mm
    footer_y = 42

    studio_pratica = pratica.studio if pratica.studio else studio

    # =========================
    # HEADER
    # =========================

    p.setFillColor(colors.HexColor("#111827"))
    p.rect(
        0,
        height - 105,
        width,
        105,
        fill=True,
        stroke=False
    )

    nome_studio = (
        studio_pratica.nome
        if studio_pratica and studio_pratica.nome
        else "Studio tecnico"
    )

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(
        margin_x,
        height - 42,
        nome_studio
    )

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#d1d5db"))
    p.drawString(
        margin_x,
        height - 60,
        "Scheda riepilogativa generata con Studio Tecnico Cloud"
    )

    if studio_pratica:

        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor("#d1d5db"))

        studio_info_y = height - 38

        info_studio = []

        if studio_pratica.indirizzo:
            info_studio.append(studio_pratica.indirizzo)

        if studio_pratica.partita_iva:
            info_studio.append(f"P.IVA {studio_pratica.partita_iva}")

        if studio_pratica.email:
            info_studio.append(studio_pratica.email)

        if studio_pratica.telefono:
            info_studio.append(studio_pratica.telefono)

        for info in info_studio[:4]:
            p.drawRightString(
                width - margin_x,
                studio_info_y,
                info
            )
            studio_info_y -= 13

    # =========================
    # TITOLO DOCUMENTO
    # =========================

    y = height - 140

    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 24)
    p.drawString(
        margin_x,
        y,
        "SCHEDA PRATICA"
    )

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#6b7280"))
    p.drawString(
        margin_x,
        y - 16,
        f"Pratica ID {pratica.id}"
    )

    p.setFillColor(colors.HexColor("#f3f4f6"))
    p.roundRect(
        width - margin_x - 170,
        y - 18,
        170,
        48,
        8,
        fill=True,
        stroke=False
    )

    p.setFillColor(colors.HexColor("#6b7280"))
    p.setFont("Helvetica-Bold", 8)
    p.drawString(
        width - margin_x - 155,
        y + 11,
        "STATO PRATICA"
    )

    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(
        width - margin_x - 155,
        y - 6,
        pratica.get_stato_display()
    )

    # =========================
    # OGGETTO PRATICA
    # =========================

    y -= 62

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Oggetto della pratica"
    )

    y -= 20

    oggetto_box_h = 58

    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.setFillColor(colors.HexColor("#f9fafb"))
    p.roundRect(
        margin_x,
        y - oggetto_box_h,
        width - 2 * margin_x,
        oggetto_box_h,
        8,
        fill=True,
        stroke=True
    )

    p.setFillColor(colors.HexColor("#111827"))
    draw_wrapped_text(
        p,
        pratica.oggetto,
        margin_x + 14,
        y - 15,
        width - 2 * margin_x - 28,
        font_name="Helvetica",
        font_size=10,
        line_height=13,
        min_y=y - oggetto_box_h + 12
    )

    y -= oggetto_box_h + 30

    # =========================
    # CLIENTE / IMMOBILE
    # =========================

    box_h = 110
    box_w = (width - 2 * margin_x - 18) / 2

    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.setFillColor(colors.white)

    p.roundRect(
        margin_x,
        y - box_h,
        box_w,
        box_h,
        10,
        fill=False,
        stroke=True
    )

    p.roundRect(
        margin_x + box_w + 18,
        y - box_h,
        box_w,
        box_h,
        10,
        fill=False,
        stroke=True
    )

    # Cliente
    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(
        margin_x + 14,
        y - 20,
        "CLIENTE"
    )

    yy = y - 40

    if pratica.cliente:

        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.HexColor("#111827"))

        yy = draw_wrapped_text(
            p,
            pratica.cliente,
            margin_x + 14,
            yy,
            box_w - 28,
            font_name="Helvetica-Bold",
            font_size=10,
            line_height=12,
            min_y=y - box_h + 12
        )

        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor("#374151"))

        if hasattr(pratica.cliente, 'email') and pratica.cliente.email and yy > y - box_h + 16:
            p.drawString(
                margin_x + 14,
                yy,
                pratica.cliente.email
            )
            yy -= 13

        if hasattr(pratica.cliente, 'telefono') and pratica.cliente.telefono and yy > y - box_h + 16:
            p.drawString(
                margin_x + 14,
                yy,
                pratica.cliente.telefono
            )

    else:

        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor("#374151"))
        p.drawString(
            margin_x + 14,
            yy,
            "-"
        )

    # Immobile
    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(
        margin_x + box_w + 32,
        y - 20,
        "IMMOBILE"
    )

    yy = y - 40

    if pratica.immobile:

        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.HexColor("#111827"))

        yy = draw_wrapped_text(
            p,
            pratica.immobile,
            margin_x + box_w + 32,
            yy,
            box_w - 28,
            font_name="Helvetica-Bold",
            font_size=10,
            line_height=12,
            min_y=y - box_h + 12
        )

        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor("#374151"))

        if hasattr(pratica.immobile, 'comune') and pratica.immobile.comune and yy > y - box_h + 16:
            p.drawString(
                margin_x + box_w + 32,
                yy,
                f"Comune: {pratica.immobile.comune}"
            )
            yy -= 13

        if hasattr(pratica.immobile, 'indirizzo') and pratica.immobile.indirizzo and yy > y - box_h + 16:
            draw_wrapped_text(
                p,
                pratica.immobile.indirizzo,
                margin_x + box_w + 32,
                yy,
                box_w - 28,
                font_size=9,
                line_height=12,
                min_y=y - box_h + 12
            )

    else:

        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor("#374151"))
        p.drawString(
            margin_x + box_w + 32,
            yy,
            "-"
        )

    y = y - box_h - 32

    # =========================
    # DATI PRATICA
    # =========================

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Dati pratica"
    )

    y -= 20

    def small_row(label, value, x, y_pos):
        p.setFont("Helvetica-Bold", 8)
        p.setFillColor(colors.HexColor("#6b7280"))
        p.drawString(
            x,
            y_pos,
            label.upper()
        )

        p.setFont("Helvetica", 10)
        p.setFillColor(colors.HexColor("#111827"))
        p.drawString(
            x,
            y_pos - 14,
            testo(value)
        )

    col_w = (width - 2 * margin_x) / 4

    small_row("Tipo pratica", pratica.tipo_pratica, margin_x, y)
    small_row("Comune", pratica.comune, margin_x + col_w, y)
    small_row("Protocollo", pratica.protocollo, margin_x + col_w * 2, y)
    small_row("Compenso", euro(pratica.compenso), margin_x + col_w * 3, y)

    y -= 50

    small_row("Data incarico", data_it(pratica.data_incarico), margin_x, y)
    small_row("Data deposito", data_it(pratica.data_deposito), margin_x + col_w, y)
    small_row("Scadenza", data_it(pratica.scadenza), margin_x + col_w * 2, y)
    small_row("Aggiornamento", data_it(now().date()), margin_x + col_w * 3, y)

    y -= 58

    # =========================
    # RIEPILOGO OPERATIVO
    # =========================

    documenti_count = pratica.documenti.count()
    parcelle_count = pratica.parcelle.count()
    attivita_count = pratica.attivita.count()
    scadenze_aperte = pratica.scadenze.filter(
        completata=False
    ).count()

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Riepilogo operativo"
    )

    y -= 22

    table_x = margin_x
    table_w = width - 2 * margin_x
    row_h = 25

    p.setFillColor(colors.HexColor("#111827"))
    p.rect(
        table_x,
        y - row_h,
        table_w,
        row_h,
        fill=True,
        stroke=False
    )

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(table_x + 12, y - 17, "Voce")
    p.drawRightString(table_x + table_w - 12, y - 17, "Totale")

    y -= row_h

    def summary_row(label, value, y_pos, fill_color=None):

        if fill_color:
            p.setFillColor(fill_color)
            p.rect(
                table_x,
                y_pos - row_h,
                table_w,
                row_h,
                fill=True,
                stroke=False
            )

        p.setStrokeColor(colors.HexColor("#e5e7eb"))
        p.line(
            table_x,
            y_pos - row_h,
            table_x + table_w,
            y_pos - row_h
        )

        p.setFillColor(colors.HexColor("#111827"))
        p.setFont("Helvetica", 10)

        p.drawString(
            table_x + 12,
            y_pos - 17,
            label
        )

        p.drawRightString(
            table_x + table_w - 12,
            y_pos - 17,
            str(value)
        )

        return y_pos - row_h

    y = summary_row("Documenti caricati", documenti_count, y)
    y = summary_row("Parcelle collegate", parcelle_count, y)
    y = summary_row("Attività registrate", attivita_count, y)
    y = summary_row(
        "Scadenze aperte",
        scadenze_aperte,
        y,
        fill_color=colors.HexColor("#f3f4f6")
    )

    y -= 28

    # =========================
    # WORKFLOW
    # =========================

    workflow_pratica = None

    try:
        workflow_pratica = pratica.workflow_pratica
    except Exception:
        workflow_pratica = None

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Workflow"
    )

    y -= 20

    p.setFillColor(colors.HexColor("#f9fafb"))
    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.roundRect(
        margin_x,
        y - 44,
        width - 2 * margin_x,
        52,
        8,
        fill=True,
        stroke=True
    )

    p.setFillColor(colors.HexColor("#374151"))

    if workflow_pratica:
        testo_workflow = f"Workflow attivo: {workflow_pratica.workflow.nome}"
    else:
        testo_workflow = "Nessun workflow automatico associato alla pratica."

    draw_wrapped_text(
        p,
        testo_workflow,
        margin_x + 14,
        y - 14,
        width - 2 * margin_x - 28,
        font_name="Helvetica",
        font_size=9,
        line_height=12,
        min_y=y - 44 + 12
    )

    y -= 72

    # =========================
    # NOTE
    # =========================

    note = pratica.note if pratica.note else "Nessuna nota inserita."

    spazio_note_minimo = 95

    if y < spazio_note_minimo + 70:

        p.setStrokeColor(colors.HexColor("#e5e7eb"))
        p.line(
            margin_x,
            footer_y + 8,
            width - margin_x,
            footer_y + 8
        )

        p.setFillColor(colors.HexColor("#6b7280"))
        p.setFont("Helvetica", 8)

        p.drawString(
            margin_x,
            footer_y - 5,
            "Documento generato con Studio Tecnico Cloud"
        )

        p.drawRightString(
            width - margin_x,
            footer_y - 5,
            f"Pratica ID {pratica.id}"
        )

        p.showPage()

        # Header pagina note
        p.setFillColor(colors.HexColor("#111827"))
        p.rect(
            0,
            height - 80,
            width,
            80,
            fill=True,
            stroke=False
        )

        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 18)
        p.drawString(
            margin_x,
            height - 38,
            "Note pratica"
        )

        p.setFont("Helvetica", 10)
        p.setFillColor(colors.HexColor("#d1d5db"))
        p.drawString(
            margin_x,
            height - 56,
            f"Scheda pratica ID {pratica.id}"
        )

        y = height - 120

    note_box_h = 85

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Note"
    )

    y -= 18

    p.setFillColor(colors.HexColor("#f9fafb"))
    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.roundRect(
        margin_x,
        y - note_box_h,
        width - 2 * margin_x,
        note_box_h,
        8,
        fill=True,
        stroke=True
    )

    p.setFillColor(colors.HexColor("#374151"))
    draw_wrapped_text(
        p,
        note,
        margin_x + 14,
        y - 14,
        width - 2 * margin_x - 28,
        font_name="Helvetica",
        font_size=9,
        line_height=12,
        min_y=y - note_box_h + 12
    )

    # =========================
    # FOOTER
    # =========================

    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.line(
        margin_x,
        footer_y + 8,
        width - margin_x,
        footer_y + 8
    )

    p.setFillColor(colors.HexColor("#6b7280"))
    p.setFont("Helvetica", 8)

    p.drawString(
        margin_x,
        footer_y - 5,
        "Documento generato con Studio Tecnico Cloud"
    )

    p.drawRightString(
        width - margin_x,
        footer_y - 5,
        f"Pratica ID {pratica.id}"
    )

    p.showPage()
    p.save()

    buffer.seek(0)

    filename = f"scheda_pratica_{pratica.id}.pdf"

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename
    )