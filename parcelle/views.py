from io import BytesIO
from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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

            if not parcella.numero_documento:

                anno = date.today().year
                prefisso = 'PAR'

                if parcella.tipo_documento == 'PREVENTIVO':
                    prefisso = 'PRE'

                elif parcella.tipo_documento == 'FATTURA':
                    prefisso = 'FAT'

                if request.user.is_superuser:
                    ultimo = Parcella.objects.filter(
                        tipo_documento=parcella.tipo_documento
                    ).count() + 1
                else:
                    ultimo = Parcella.objects.filter(
                        pratica__studio=studio,
                        tipo_documento=parcella.tipo_documento
                    ).count() + 1

                parcella.numero_documento = f'{prefisso}-{anno}-{ultimo}'

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
    logo_path = "static/img/logo.png"

    try:
        p.drawImage(
            logo_path,
            50,
            height - 85,
            width=90,
            height=45,
            preserveAspectRatio=True,
            mask='auto'
        )
    except Exception:
        pass

    p.setFont("Helvetica-Bold", 18)
    p.drawString(160, height - 55, "Gestionale Studio Tecnico")

    p.setFont("Helvetica", 10)
    p.drawString(160, height - 73, "Scheda parcella / riepilogo compenso")

    p.line(50, height - 105, width - 50, height - 105)

    y = height - 145

    p.setFont("Helvetica-Bold", 17)
    p.drawString(50, y, "Riepilogo parcella")

    y -= 35

    def section_title(title, y_pos):

        p.setFillColorRGB(0.07, 0.09, 0.15)

        p.rect(
            50,
            y_pos - 6,
            width - 100,
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
            190,
            y_pos,
            str(value) if value else "-"
        )

        return y_pos - 22

    y = section_title("DATI PARCELLA", y)

    y = row("Numero documento", parcella.numero_documento, y)
    y = row("ID interno", parcella.id, y)
    y = row("Tipo documento", parcella.get_tipo_documento_display(), y)
    y = row("Descrizione", parcella.descrizione, y)
    y = row("Stato pagamento", parcella.get_stato_display(), y)
    y = row("Data emissione", parcella.data_emissione, y)
    y = row("Data pagamento", parcella.data_pagamento, y)

    y -= 10
    y = section_title("PRATICA COLLEGATA", y)

    y = row("Pratica", parcella.pratica, y)

    if hasattr(parcella.pratica, 'cliente'):
        y = row("Cliente", parcella.pratica.cliente, y)

    if hasattr(parcella.pratica, 'comune'):
        y = row("Comune", parcella.pratica.comune, y)

    y -= 10
    y = section_title("IMPORTI", y)

    y = row("Importo totale", f"Euro {parcella.importo}", y)
    y = row("IVA", f"{parcella.iva}%", y)

    totale_con_iva = parcella.importo + (
        parcella.importo * parcella.iva / 100
    )

    y = row("Totale con IVA", f"Euro {totale_con_iva}", y)
    y = row("Importo pagato", f"Euro {parcella.importo_pagato}", y)

    saldo_residuo = parcella.importo - parcella.importo_pagato

    y = row("Saldo residuo", f"Euro {saldo_residuo}", y)

    y -= 10
    y = section_title("NOTE", y)

    note = parcella.note if parcella.note else "-"

    p.setFont("Helvetica", 10)

    max_chars = 90
    note_lines = [
        note[i:i + max_chars]
        for i in range(0, len(note), max_chars)
    ]

    for line in note_lines:

        if y < 80:
            p.showPage()
            y = height - 70

        p.drawString(60, y, line)
        y -= 18

    p.line(50, 55, width - 50, 55)

    p.setFont("Helvetica", 8)

    p.drawString(
        50,
        40,
        "Documento generato automaticamente dal Gestionale Studio Tecnico"
    )

    p.drawRightString(
        width - 50,
        40,
        f"Parcella ID {parcella.id}"
    )

    p.showPage()
    p.save()

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"parcella_{parcella.id}.pdf"
    )