from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse

from reportlab.pdfgen import canvas

from accounts.decorators import group_required

from .models import Pratica
from .forms import PraticaForm

from attivita.models import Attivita


@login_required
def lista_pratiche(request):

    pratiche = Pratica.objects.all().order_by('-id')

    context = {
        'pratiche': pratiche,
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

    documenti = pratica.documenti.all()

    parcelle = pratica.parcelle.all()

    attivita = pratica.attivita.all().order_by('-data')

    context = {
        'pratica': pratica,
        'documenti': documenti,
        'parcelle': parcelle,
        'attivita': attivita,
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

            Attivita.objects.create(
                utente=request.user,
                tipo='CREAZIONE',
                descrizione=f'Creata pratica: {pratica.oggetto}'
            )

            return redirect('lista_pratiche')

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
        utente=request.user,
        tipo='PDF',
        descrizione=f'Generato PDF pratica: {pratica.oggetto}'
    )

    buffer = BytesIO()

    p = canvas.Canvas(buffer)

    p.setTitle(f"Scheda pratica {pratica.id}")

    width, height = 595, 842

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