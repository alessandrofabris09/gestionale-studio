from io import BytesIO
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import FileResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

from studi.utils import get_studio_utente
from studi.permessi import (
    puo_vedere_parcelle,
    puo_modificare_parcelle,
    puo_eliminare_parcelle,
)

from .models import Parcella
from .forms import ParcellaForm

from attivita.models import Attivita


def accesso_negato(request):
    """
    Pagina grafica di blocco accesso.
    """

    return render(
        request,
        'errors/accesso_negato.html',
        status=403
    )


def get_parcelle_queryset(request):
    """
    Restituisce le parcelle visibili dall'utente.

    Superuser:
    - vede tutte le parcelle

    Utente normale:
    - vede solo le parcelle dello studio collegato
    """

    studio = get_studio_utente(request)

    if request.user.is_superuser:
        return Parcella.objects.all()

    return Parcella.objects.filter(
        pratica__studio=studio
    )


@login_required
def lista_parcelle(request):

    if not puo_vedere_parcelle(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    parcelle = get_parcelle_queryset(request).order_by('-id')

    ricerca = request.GET.get('ricerca')

    if ricerca:

        parcelle = parcelle.filter(
            Q(descrizione__icontains=ricerca) |
            Q(pratica__oggetto__icontains=ricerca) |
            Q(pratica__cliente__nome__icontains=ricerca) |
            Q(numero_documento__icontains=ricerca)
        )

    return render(
        request,
        'parcelle/lista_parcelle.html',
        {
            'parcelle': parcelle,
            'ricerca': ricerca,
        }
    )


@login_required
def nuova_parcella(request):

    if not puo_modificare_parcelle(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.method == 'POST':

        form = ParcellaForm(
            request.POST,
            studio=studio
        )

        if form.is_valid():

            parcella = form.save(commit=False)

            if not request.user.is_superuser:
                if parcella.pratica.studio != studio:
                    return accesso_negato(request)

            if parcella.iva is None:
                parcella.iva = 0

            parcella.save()

            Attivita.objects.create(
                pratica=parcella.pratica,
                utente=request.user,
                tipo='PARCELLA',
                descrizione=(
                    f'Creata {parcella.get_tipo_documento_display()}: '
                    f'{parcella.numero_documento}'
                )
            )

            return redirect('lista_parcelle')

        else:

            print(form.errors)

    else:

        form = ParcellaForm(
            studio=studio
        )

    return render(
        request,
        'parcelle/nuova_parcella.html',
        {
            'form': form
        }
    )


@login_required
def modifica_parcella(request, parcella_id):

    if not puo_modificare_parcelle(request):
        return accesso_negato(request)

    parcella = get_object_or_404(
        get_parcelle_queryset(request),
        id=parcella_id
    )

    studio = get_studio_utente(request)

    if request.method == 'POST':

        form = ParcellaForm(
            request.POST,
            instance=parcella,
            studio=studio
        )

        if form.is_valid():

            parcella = form.save(commit=False)

            if not request.user.is_superuser:
                if parcella.pratica.studio != studio:
                    return accesso_negato(request)

            parcella.save()

            Attivita.objects.create(
                pratica=parcella.pratica,
                utente=request.user,
                tipo='MODIFICA',
                descrizione=(
                    f'Modificata parcella: '
                    f'{parcella.numero_documento}'
                )
            )

            return redirect('lista_parcelle')

    else:

        form = ParcellaForm(
            instance=parcella,
            studio=studio
        )

    return render(
        request,
        'parcelle/modifica_parcella.html',
        {
            'form': form,
            'parcella': parcella,
        }
    )


@login_required
def elimina_parcella(request, parcella_id):

    if not puo_eliminare_parcelle(request):
        return accesso_negato(request)

    parcella = get_object_or_404(
        get_parcelle_queryset(request),
        id=parcella_id
    )

    if request.method == 'POST':

        Attivita.objects.create(
            pratica=parcella.pratica,
            utente=request.user,
            tipo='ELIMINAZIONE',
            descrizione=(
                f'Eliminata parcella: '
                f'{parcella.numero_documento}'
            )
        )

        parcella.delete()

        return redirect('lista_parcelle')

    return render(
        request,
        'parcelle/elimina_parcella.html',
        {
            'parcella': parcella
        }
    )


def euro(value):
    """
    Formatta un valore economico in euro.
    """

    if value is None:
        value = Decimal('0.00')

    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_it(value):
    """
    Formatta una data in formato italiano.
    """

    if not value:
        return "-"

    return value.strftime('%d/%m/%Y')


def testo(value):
    """
    Restituisce testo sicuro per PDF.
    """

    if value is None or value == '':
        return "-"

    return str(value)


def draw_wrapped_text(p, text, x, y, max_width, font_name="Helvetica", font_size=9, line_height=13):
    """
    Scrive testo multilinea semplice entro una larghezza massima.
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
            p.drawString(x, y, line)
            y -= line_height
            line = word

    if line:
        p.drawString(x, y, line)
        y -= line_height

    return y


@login_required
def pdf_parcella(request, parcella_id):

    if not puo_vedere_parcelle(request):
        return accesso_negato(request)

    parcella = get_object_or_404(
        get_parcelle_queryset(request),
        id=parcella_id
    )

    Attivita.objects.create(
        pratica=parcella.pratica,
        utente=request.user,
        tipo='PDF',
        descrizione=(
            f'Generato PDF parcella: '
            f'{parcella.numero_documento}'
        )
    )

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    margin_x = 20 * mm

    studio = parcella.pratica.studio if parcella.pratica else None
    cliente = parcella.pratica.cliente if parcella.pratica and parcella.pratica.cliente else None

    tipo_documento = parcella.get_tipo_documento_display().upper()

    imponibile = parcella.imponibile
    importo_iva = parcella.importo_iva
    totale = parcella.totale_con_iva
    pagato = parcella.importo_pagato or Decimal('0.00')
    saldo = parcella.saldo_residuo

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

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(
        margin_x,
        height - 42,
        "Studio Tecnico Cloud"
    )

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#d1d5db"))
    p.drawString(
        margin_x,
        height - 60,
        "Documento generato dal gestionale per studi tecnici"
    )

    if studio:

        p.setFont("Helvetica-Bold", 11)
        p.setFillColor(colors.white)
        p.drawRightString(
            width - margin_x,
            height - 40,
            testo(studio.nome)
        )

        p.setFont("Helvetica", 9)
        p.setFillColor(colors.HexColor("#d1d5db"))

        studio_info_y = height - 57

        if studio.indirizzo:
            p.drawRightString(
                width - margin_x,
                studio_info_y,
                studio.indirizzo
            )
            studio_info_y -= 13

        if studio.partita_iva:
            p.drawRightString(
                width - margin_x,
                studio_info_y,
                f"P.IVA {studio.partita_iva}"
            )
            studio_info_y -= 13

        if studio.email:
            p.drawRightString(
                width - margin_x,
                studio_info_y,
                studio.email
            )

    # =========================
    # TITOLO DOCUMENTO
    # =========================

    y = height - 140

    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 24)
    p.drawString(
        margin_x,
        y,
        tipo_documento
    )

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#6b7280"))
    p.drawString(
        margin_x,
        y - 16,
        f"Documento n. {testo(parcella.numero_documento)}"
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
        "STATO PAGAMENTO"
    )

    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(
        width - margin_x - 155,
        y - 6,
        parcella.get_stato_display()
    )

    # =========================
    # DATI CLIENTE / PRATICA
    # =========================

    y -= 70

    box_h = 115
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

    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(
        margin_x + 14,
        y - 20,
        "DESTINATARIO"
    )

    p.setFont("Helvetica", 9)
    p.setFillColor(colors.HexColor("#374151"))

    yy = y - 40

    if cliente:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(
            margin_x + 14,
            yy,
            testo(cliente)
        )
        yy -= 15

        p.setFont("Helvetica", 9)

        if hasattr(cliente, 'email') and cliente.email:
            p.drawString(
                margin_x + 14,
                yy,
                cliente.email
            )
            yy -= 13

        if hasattr(cliente, 'telefono') and cliente.telefono:
            p.drawString(
                margin_x + 14,
                yy,
                cliente.telefono
            )
            yy -= 13

    else:

        p.drawString(
            margin_x + 14,
            yy,
            "-"
        )

    p.setFillColor(colors.HexColor("#111827"))
    p.setFont("Helvetica-Bold", 11)
    p.drawString(
        margin_x + box_w + 32,
        y - 20,
        "PRATICA COLLEGATA"
    )

    p.setFont("Helvetica", 9)
    p.setFillColor(colors.HexColor("#374151"))

    yy = y - 40

    p.setFont("Helvetica-Bold", 10)
    p.drawString(
        margin_x + box_w + 32,
        yy,
        testo(parcella.pratica)
    )

    yy -= 15
    p.setFont("Helvetica", 9)

    if parcella.pratica and parcella.pratica.comune:
        p.drawString(
            margin_x + box_w + 32,
            yy,
            f"Comune: {parcella.pratica.comune}"
        )
        yy -= 13

    if parcella.pratica and parcella.pratica.oggetto:
        yy = draw_wrapped_text(
            p,
            parcella.pratica.oggetto,
            margin_x + box_w + 32,
            yy,
            box_w - 28,
            font_size=9,
            line_height=12
        )

    # =========================
    # DATI DOCUMENTO
    # =========================

    y = y - box_h - 35

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Dati documento"
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

    small_row(
        "Data emissione",
        data_it(parcella.data_emissione),
        margin_x,
        y
    )

    small_row(
        "Data scadenza",
        data_it(parcella.data_scadenza),
        margin_x + col_w,
        y
    )

    small_row(
        "Data pagamento",
        data_it(parcella.data_pagamento),
        margin_x + col_w * 2,
        y
    )

    small_row(
        "ID interno",
        parcella.id,
        margin_x + col_w * 3,
        y
    )

    y -= 55

    # =========================
    # DESCRIZIONE PRESTAZIONE
    # =========================

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Descrizione prestazione"
    )

    y -= 22

    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.setFillColor(colors.HexColor("#f9fafb"))
    p.roundRect(
        margin_x,
        y - 58,
        width - 2 * margin_x,
        70,
        8,
        fill=True,
        stroke=True
    )

    p.setFillColor(colors.HexColor("#111827"))

    draw_wrapped_text(
        p,
        parcella.descrizione,
        margin_x + 14,
        y - 12,
        width - 2 * margin_x - 28,
        font_name="Helvetica",
        font_size=10,
        line_height=13
    )

    y -= 95

    # =========================
    # TABELLA IMPORTI
    # =========================

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Riepilogo economico"
    )

    y -= 22

    table_x = margin_x
    table_w = width - 2 * margin_x
    row_h = 28

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
    p.drawString(table_x + 12, y - 18, "Voce")
    p.drawRightString(table_x + table_w - 12, y - 18, "Importo")

    y -= row_h

    def amount_row(label, value, y_pos, bold=False, fill_color=None):

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

        if bold:
            p.setFont("Helvetica-Bold", 10)
        else:
            p.setFont("Helvetica", 10)

        p.drawString(
            table_x + 12,
            y_pos - 18,
            label
        )

        p.drawRightString(
            table_x + table_w - 12,
            y_pos - 18,
            value
        )

        return y_pos - row_h

    y = amount_row(
        "Imponibile",
        euro(imponibile),
        y
    )

    y = amount_row(
        f"IVA {parcella.iva}%",
        euro(importo_iva),
        y
    )

    y = amount_row(
        "Totale documento",
        euro(totale),
        y,
        bold=True,
        fill_color=colors.HexColor("#f3f4f6")
    )

    y = amount_row(
        "Importo pagato",
        euro(pagato),
        y
    )

    y = amount_row(
        "Saldo residuo",
        euro(saldo),
        y,
        bold=True,
        fill_color=colors.HexColor("#ecfdf5")
    )

    y -= 35

    # =========================
    # NOTE
    # =========================

    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(colors.HexColor("#111827"))
    p.drawString(
        margin_x,
        y,
        "Note"
    )

    y -= 22

    note = parcella.note if parcella.note else "Nessuna nota inserita."

    p.setFillColor(colors.HexColor("#f9fafb"))
    p.roundRect(
        margin_x,
        y - 58,
        width - 2 * margin_x,
        70,
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
        line_height=12
    )

    # =========================
    # FOOTER
    # =========================

    p.setStrokeColor(colors.HexColor("#e5e7eb"))
    p.line(
        margin_x,
        45,
        width - margin_x,
        45
    )

    p.setFillColor(colors.HexColor("#6b7280"))
    p.setFont("Helvetica", 8)

    p.drawString(
        margin_x,
        30,
        "Documento generato automaticamente da Studio Tecnico Cloud"
    )

    p.drawRightString(
        width - margin_x,
        30,
        f"{tipo_documento} ID {parcella.id}"
    )

    p.showPage()
    p.save()

    buffer.seek(0)

    filename = (
        f"{parcella.get_tipo_documento_display().lower()}_"
        f"{parcella.numero_documento or parcella.id}.pdf"
    )

    filename = filename.replace(
        " ",
        "_"
    ).replace(
        "/",
        "-"
    )

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename
    )